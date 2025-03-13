import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

from person import PersonCollection
from resource import ResourceCollection
from relationship import RelationshipCollection


def main():
    stats = []

    params = {
        'start_population': 500,
        'start_resources': 500,
        'turns': 2000,
        'age_std_dev': 15,
        'age_mean': 40,
        'max_age': 80,
        'max_age_min': 60,
        'max_age_max': 80,
        'child_chance': 0.07,
        'max_children_min': 1,
        'max_children_max': 3,
        'need_per_turn': 2,
        'stockpiling_need_per_turn_min': 0,
        'stockpiling_need_per_turn_max': 3,
        'min_reproduce_age': 18,
        'max_reproduce_age': 40,
        'resource_max_amount': 2,
        'find_resources_count': 5,
        'grow_amount': 1,
        'max_relationships': 5,
        'default_relationship_strength': 0.5,
        'relationship_increment': 0.1,
        'max_debt': 0.7,
        'min_rel_build_age': 16,
        'rel_build_threshold_years': 5
    }

    # Create resource collection with random amounts
    resource_collection = ResourceCollection(params, params['start_resources'])

    # Create a collection of relationships between people
    relationship_collection = RelationshipCollection(params)

    # Create a collection of people of random ages
    people = PersonCollection(params, params['start_population'], resource_collection, relationship_collection).people

    # Provide the relationship collection with the people
    relationship_collection.people = people

    try:
        for turn in tqdm(range(0, params['turns']), desc='Simulating', unit='turns'):
            children = []

            # People meet their needs and have children
            for person in people:
                child = person.lives()
                if child:
                    children.append(child)

            # Grow the resources
            resource_collection.grow()

            # Append any children to people list
            people += children

            num_alive_people = len([person for person in people if person.alive])

            if num_alive_people == 0:
                break

            # Collect stats
            stats.append({
                'turn': turn,
                'people': len(people),
                'alive': num_alive_people,
                'dead': len(people) - num_alive_people,
                'resources': resource_collection.total_resources(),
                'average_number_of_children': sum([len(person.progeny) for person in people if person.alive]) / num_alive_people,
                'average_age': sum([person.age for person in people if person.alive]) / num_alive_people,
                'children_born_per_year': len(children),
                'average_stockpile': sum([person.stockpile for person in people if person.alive]) / num_alive_people,
                'total_stockpile': sum([person.stockpile for person in people if person.alive]),
                'total_stockpile_need_per_turn': sum([person.stockpiling_need_per_turn for person in people if person.alive]),
                'total_children_with_alive_parents': sum([len(person.progeny) for person in people if person.alive])
            })
    except KeyboardInterrupt:
        print("\nLoop interrupted. Continuing with the rest of the program.")

    df = pd.DataFrame(stats)

    df.plot(x='turn', y=['alive'])
    plt.show()

    df.plot(x='turn', y=['children_born_per_year'])
    plt.show()

    df.plot(x='turn', y=['average_number_of_children'])
    plt.show()

    df.plot(x='turn', y=['average_age'])
    plt.show()

    df.plot(x='turn', y=['resources'])
    plt.show()

    df.plot(x='turn', y=['total_children_with_alive_parents'])
    plt.show()

    df.plot(x='turn', y=['average_stockpile'])
    plt.show()

    df.plot(x='turn', y=['total_stockpile_need_per_turn'])
    plt.show()

    df.plot(x='turn', y=['total_stockpile'])
    plt.show()

    # Plot a histogram of the number of children of the people who are still alive
    children = [len(person.progeny) for person in people if person.alive]
    plt.hist(children, bins=range(0, 10))
    plt.title('Number of children')
    plt.show()

    # Plot a histogram of the ages of the people who are still alive
    ages = [person.age for person in people if person.alive]
    plt.hist(ages, bins=range(0, 100, 5))
    plt.title('Alive ages')
    plt.show()

    # Plot a histogram of the ages of stockpile sizes of the people who are still alive
    stockpiles = [person.stockpile for person in people if person.alive]
    if len(stockpiles) > 0:
        max_stockpile = max(stockpiles)
        plt.hist(stockpiles, bins=range(0, max_stockpile, 5))
        plt.title('Stockpile sizes')
        plt.show()

    # Plot a histogram of relationship strengths
    strengths = [relationship.debt for person in people if person.alive for relationship in person.relationships]
    plt.hist(strengths, bins=10)
    plt.title('Relationship strengths')
    plt.show()

    # Plot a histogram of the number of relationships of living people
    relationships = [len(person.relationships) for person in people if person.alive]
    plt.hist(relationships, bins=range(0, 10))
    plt.title('Number of relationships')
    plt.show()

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
    children = [len(person.progeny) for person in people if person.alive]
    stockpiles = [person.stockpile for person in people if person.alive]
    plt.scatter(children, stockpiles)
    plt.xlabel('Number of children')
    plt.ylabel('Stockpile size')
    plt.title('Correlation between number of children and stockpile size')
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

if __name__ == '__main__':
    main()







