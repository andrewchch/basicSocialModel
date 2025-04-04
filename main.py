import matplotlib.pyplot as plt
import pandas as pd
import cProfile
import pstats
import random

from tqdm import tqdm

from epoch import Epoch
from parameters import Parameters
from person import PersonCollection, ResourcesMetEnum, HowDiedEnum
from resource import ResourceCollection
from relationship import RelationshipCollection
from performance import analyse


def get_filter_length(lmb, a):
    return sum(1 for _ in (filter(lmb, a)))


def main():
    stats = []

    charts = {
        'alive': True,
        'children_born_per_year': True,
        'average_number_of_children': False,
        'average_age': False,
        'average_age_of_death': True,
        'resources': True,
        'total_children_with_alive_parents': False,
        'average_stockpile': True,
        'total_stockpile_need_per_turn': False,
        'total_stockpile': False,
        'num_children_by_stockpile': False,
        'num_children_histogram': True,
        'needs_met_chart': True,
        'relationship_strengths': False,
        'relationship_counts': False,
        'ages_histogram': False,
        'stockpile_sizes_histogram': True,
        'resources_available': False,
        'how_died': True,
        'people_to_resources_ratios': True,
        }

    # Turn all charts off
    # charts = {k: False for k in charts.keys()}

    # Create some parameters
    params = Parameters()

    # Create resource collection with random amounts
    resource_collection = ResourceCollection(params, params['start_resources'])

    # Create a collection of relationships between people
    relationship_collection = RelationshipCollection(params)

    # Create a collection of people of random ages
    pc = PersonCollection(params, params['start_population'], resource_collection, relationship_collection)
    people = pc.people
    relationship_collection.person_collection = pc

    # Chart the distribution of ages
    """
    ages = [person.age for person in people]
    plt.hist(ages, bins=range(0, 100, 5))
    plt.title('Ages')
    plt.show()
    """

    # Provide the relationship collection with the people
    relationship_collection.people = pc.people

    # Add epochs
    # params.add_epoch(Epoch(500, 2000, {'grow_chance': 0.5}))
    # params.add_epoch(Epoch(500, 2000, {'stockpiling_need_per_turn_max': 0}))
    # params.add_epoch(Epoch(500, 2000, {'find_resources_count': 2}))
    # params.add_epoch(Epoch(500, 2000, {'need_per_turn': 4}))

    try:
        for turn in tqdm(range(0, params['turns']), desc='Simulating', unit='turns'):
            children = []

            params['turn'] = turn

            # Update the parameters for this turn
            params.apply_epochs(turn)

            # People meet their needs and have children
            for person in pc.shuffled_alive_people:
                child = person.lives()
                if child:
                    children.append(child)

            # Grow the resources
            resource_collection.grow()

            alive_people = [p for p in pc.alive_people]
            num_alive_people = len(alive_people)

            if num_alive_people == 0:
                break

            # Get the number of people alive in this turn and the number of people who have died
            died_this_turn = list(filter(lambda p: p.died == turn, pc.people))
            num_people_acted_in_turn = num_alive_people + len(died_this_turn)

            # Stats for percentages of people having their needs met from different sources
            needs_met_from_resources = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_RESOURCES, alive_people)/num_people_acted_in_turn
            needs_met_from_stockpile = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_STOCKPILE, alive_people)/num_people_acted_in_turn
            needs_met_from_relationships = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_RELATIONSHIPS, alive_people)/num_people_acted_in_turn
            needs_from_parent = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_PARENT, alive_people)/num_people_acted_in_turn
            needs_not_met_died = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.NOT_MET_DIED, died_this_turn)/num_people_acted_in_turn

            # Get counts of how people died in this turn
            num_starved = get_filter_length(lambda p: p.how_died == HowDiedEnum.STARVED, died_this_turn)
            num_old_age = get_filter_length(lambda p: p.how_died == HowDiedEnum.OLD_AGE, died_this_turn)

            # Calculate the total of all stockpiles of alive people plus all resources
            total_stockpile = sum([person.stockpile for person in alive_people])
            total_resources = resource_collection.total_resources()
            total_stockpile_and_resources = total_stockpile + total_resources

            # Collect stats
            stats.append({
                'turn': turn,
                'people': len(pc.people),
                'alive': num_alive_people,
                'dead': len(pc.people) - num_alive_people,
                'average_age_of_death': sum([person.age for person in died_this_turn]) / len(died_this_turn) if len(died_this_turn) > 0 else 0,
                'resources': resource_collection.total_resources(),
                'average_number_of_children': sum([len(person.progeny) for person in alive_people]) / num_alive_people,
                'average_age': sum([person.age for person in alive_people]) / num_alive_people,
                'children_born_per_year': len(children),
                'average_stockpile': sum([person.stockpile for person in alive_people]) / num_alive_people,
                'total_stockpile': sum([person.stockpile for person in alive_people]),
                'pct_with_stockpile': get_filter_length(lambda p: p.stockpile > 0, alive_people) / num_alive_people,
                'total_stockpile_need_per_turn': sum([person.stockpiling_need_per_turn for person in alive_people]),
                'total_children_with_alive_parents': sum([len(person.progeny) for person in alive_people]),
                'needs_met_from_resources': needs_met_from_resources,
                'needs_met_from_stockpile': needs_met_from_stockpile,
                'needs_met_from_relationships': needs_met_from_relationships,
                'needs_from_parent': needs_from_parent,
                'needs_not_met_died': needs_not_met_died,
                'resources_available': [person.resources_available for person in people if person.alive or (person.needs_met == ResourcesMetEnum.NOT_MET_DIED and person.died == turn)],
                'num_starved': num_starved,
                'num_old_age': num_old_age,
                'ratio_of_needs_to_resources': sum(
                    [person.need_per_turn for person in alive_people])/total_stockpile_and_resources,
                'ratio_of_alive_people_to_resources': num_alive_people / total_stockpile_and_resources,
                'ratio_of_stockpiles_to_resources': total_stockpile / total_resources
            })

            # Append any children to people list. We do this last because the children are not alive until the next
            # turn, and we don't want to include them in the stats
            for child in children:
                pc.add(child)

    except KeyboardInterrupt:
        print("\nLoop interrupted. Continuing with the rest of the program.")

    df = pd.DataFrame(stats)

    if charts['alive']:
        df.plot(x='turn', y=['alive'])
        plt.show()

    if charts['how_died']:
        df.plot(x='turn', y=['num_starved', 'num_old_age'])
        plt.show()

    if charts['average_age_of_death']:
        df.plot(x='turn', y=['average_age_of_death'])
        plt.show()

    if charts['children_born_per_year']:
        df.plot(x='turn', y=['children_born_per_year'])
        plt.show()

    if charts['average_number_of_children']:
        df.plot(x='turn', y=['average_number_of_children'])
        plt.show()

    if charts['average_age']:
        df.plot(x='turn', y=['average_age'])
        plt.show()

    if charts['resources']:
        df.plot(x='turn', y=['resources'])
        plt.show()

    if charts['total_children_with_alive_parents']:
        df.plot(x='turn', y=['total_children_with_alive_parents'])
        plt.show()

    if charts['average_stockpile']:
        df.plot(x='turn', y=['average_stockpile'])
        plt.show()

    if charts['total_stockpile_need_per_turn']:
        df.plot(x='turn', y=['total_stockpile_need_per_turn'])
        plt.show()

    if charts['total_stockpile']:
        df.plot(x='turn', y=['total_stockpile'])
        plt.show()

    # Plot a histogram of the number of children of the people who are still alive and of child-bearing age
    if charts['num_children_histogram']:
        children = [len(person.progeny) for person in people if person.alive and
                    params['min_reproduce_age'] <= person.age <= params['max_reproduce_age']]
        plt.hist(children, bins=range(0, 10))
        plt.title('Number of children')
        plt.show()

    # Plot a histogram of the ages of the people who are still alive
    if charts['ages_histogram']:
        ages = [person.age for person in people if person.alive]
        plt.hist(ages, bins=range(0, 100, 5))
        plt.title('Alive ages')
        plt.show()

    # Plot a histogram of stockpile sizes of the people who are still alive
    if charts['stockpile_sizes_histogram']:
        stockpiles = [person.stockpile for person in people if person.alive]
        if len(stockpiles) > 0:
            max_stockpile = max(stockpiles)
            plt.hist(stockpiles, bins=range(0, int(max_stockpile) + 1, 5))
            plt.title('Stockpile sizes')
            plt.show()

    # Plot a histogram of the number of relationships of living people
    if charts['relationship_counts']:
        relationships = [len(person.relationships) for person in people if person.alive]
        plt.hist(relationships, bins=range(0, 10))
        plt.title('Number of relationships')
        plt.show()

    if charts['relationship_strengths']:
        # Get the mean strength of a relationship and its inverse relationship
        strengths = []
        for person in [p for p in people if p.alive]:
            for relationship in person.relationships:
                strengths.append(relationship.debt)
                inverse_relationship = relationship.relationship_collection.get(relationship.person2, relationship.person1)
                if inverse_relationship:
                    strengths.append(0.5 * (relationship.debt + inverse_relationship.debt))

        # Plot a histogram of the mean strength of a relationship and its inverse relationship
        plt.hist(strengths, bins=10)
        plt.title('Mean relationship strengths')
        plt.show()

    # Plot a correlation between the number of children and the stockpile size
    if charts['num_children_by_stockpile']:
        children = [len(person.progeny) for person in people if person.alive]
        stockpiles = [person.stockpile for person in people if person.alive]
        plt.scatter(children, stockpiles)
        plt.xlabel('Number of children')
        plt.ylabel('Stockpile size')
        plt.title('Correlation between number of children and stockpile size')
        plt.show()

    # Display a line chart of the values of needs_met_from_resources, needs_met_from_stockpile,
    # and needs_met_from_relationships
    if charts['needs_met_chart']:
        df.plot(x='turn', y=['pct_with_stockpile', 'needs_met_from_resources', 'needs_met_from_stockpile',
                             'needs_met_from_relationships', 'needs_from_parent', 'needs_not_met_died'])
        plt.show()

    # Create a boxplot of "resources_available" stat for each turn where the x-axis is the turn value and the y axis is
    # the resources available
    if charts['resources_available']:
        # Flatten the data
        flattened_data = []
        for entry in stats:
            turn = entry['turn']
            for resource in entry['resources_available']:
                flattened_data.append({'turn': turn, 'resources_available': resource})

        # Create a DataFrame
        ra_df = pd.DataFrame(flattened_data)

        # Create the boxplot
        ra_df.boxplot(column='resources_available', by='turn', grid=False)
        plt.title('Resources Available per Turn')
        plt.suptitle('')  # Suppress the default title to avoid overlap
        plt.xlabel('Turn')
        plt.ylabel('Resources Available')
        plt.show()

        # Plot the mean resources available per turn
        ra_df.groupby('turn').mean().plot()
        plt.title('Mean Resources Available per Turn')
        plt.xlabel('Turn')
        plt.ylabel('Mean Resources Available')
        plt.show()

    # Create a chart of people and needs to resources ratios
    if charts['people_to_resources_ratios']:
        df.plot(x='turn', y=['ratio_of_needs_to_resources',
                             'ratio_of_alive_people_to_resources',
                             'ratio_of_stockpiles_to_resources'])
        plt.show()

    # List the number of distinct values of the number of children and the nuber of people with that number of children
    children_counts = {}
    for person in people:
        if person.alive:
            children_count = len(person.progeny)
            if children_count not in children_counts:
                children_counts[children_count] = 0
            children_counts[children_count] += 1

    print(children_counts)

    # Get the number of relationships with history entries
    relationships = [relationship for person in people if person.alive for relationship in person.relationships]
    relationships_with_history = [relationship for relationship in relationships if len(relationship.history) > 0]
    print(f'Number of relationships with history: {len(relationships_with_history)}')

    # Calculate a Gini coefficient for the stockpile sizes of alive people
    stockpiles = [person.stockpile for person in people if person.alive]
    if len(stockpiles) > 0:
        stockpiles.sort()
        n = len(stockpiles)
        gini_numerator = 2 * sum((i + 1) * stockpiles[i] for i in range(n))
        gini_denominator = n * sum(stockpiles)
        gini = (n + 1 - (gini_numerator / gini_denominator)) / n
        print(f'Gini coefficient for stockpile sizes: {gini}')

    # Print the number of people in total
    print(f'Total number of people: {len(pc.people)}')


if __name__ == '__main__':
    # Capture the stats
    """
    stats_file = "sim_stats"
    cProfile.run("main()", stats_file)
    p = pstats.Stats(stats_file)

    # Analyse the file
    df = analyse(stats_file)

    # Pickle the stats
    df.to_pickle("sim_stats.pkl")
    df.to_csv("sim_stats.csv")
    """
    main()







