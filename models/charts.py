import matplotlib.pyplot as plt
import pandas as pd


class Charts:
    def __init__(self, stats, params, person_collection):
        self.stats = stats
        self.people = person_collection.people
        self.params = params
        self.pc = person_collection
        
        self.charts = {
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
            'child_chance': True,
            'min_stockpile_for_breeding_avg': True,
            'min_stockpile_for_breeding': True,
            'died_this_turn_ages': True,
        }

    # Turn all self.charts off
    # self.charts = {k: False for k in self.charts.keys()}
        
    def display(self):
        df = pd.DataFrame(self.stats)

        if self.charts['alive']:
            df.plot(x='turn', y=['alive'])
            plt.show()

        if self.charts['how_died']:
            df.plot(x='turn', y=['num_starved', 'num_old_age'])
            plt.show()

        if self.charts['died_this_turn_ages']:
            # Each value of died_this_turn is a list of values, so we need to flatten it
            flattened_data = []
            for entry in self.stats:
                turn = entry['turn']
                for value in entry['died_this_turn_ages']:
                    flattened_data.append({'turn': turn, 'died_this_turn_ages': value})

            # Create a DataFrame
            flatted_df = pd.DataFrame(flattened_data)

            # Create the scatter plot
            plt.figure(figsize=(10, 6))
            plt.scatter(flatted_df['turn'], flatted_df['died_this_turn_ages'], alpha=0.02)
            plt.show()

        if self.charts['average_age_of_death']:
            df.plot(x='turn', y=['average_age_of_death'])
            plt.show()

        if self.charts['children_born_per_year']:
            df.plot(x='turn', y=['children_born_per_year'])
            plt.show()

        if self.charts['average_number_of_children']:
            df.plot(x='turn', y=['average_number_of_children'])
            plt.show()

        if self.charts['average_age']:
            df.plot(x='turn', y=['average_age'])
            plt.show()

        if self.charts['resources']:
            df.plot(x='turn', y=['resources'])
            plt.show()

        if self.charts['total_children_with_alive_parents']:
            df.plot(x='turn', y=['total_children_with_alive_parents'])
            plt.show()

        if self.charts['child_chance']:
            df.plot(x='turn', y=['average_child_chance'])
            plt.show()

        if self.charts['min_stockpile_for_breeding']:
            df.plot(x='turn', y=['min_stockpile_for_breeding_avg'])
            plt.show()

        # Draw a scatter plot of the min stockpile for breeding values by turn, where each point is of opacity 0.1
        if self.charts['min_stockpile_for_breeding']:
            # Each value of min_stockpile_for_breeding is a list of values, so we need to flatten it
            flattened_data = []
            for entry in self.stats:
                turn = entry['turn']
                for value in entry['min_stockpile_for_breeding']:
                    flattened_data.append({'turn': turn, 'min_stockpile_for_breeding': value})

            # Create a DataFrame
            flatted_df = pd.DataFrame(flattened_data)

            # Create the scatter plot
            plt.figure(figsize=(10, 6))
            plt.scatter(flatted_df['turn'], flatted_df['min_stockpile_for_breeding'], alpha=0.02)
            plt.show()

        if self.charts['average_stockpile']:
            df.plot(x='turn', y=['average_stockpile'])
            plt.show()

        if self.charts['total_stockpile_need_per_turn']:
            df.plot(x='turn', y=['total_stockpile_need_per_turn'])
            plt.show()

        if self.charts['total_stockpile']:
            df.plot(x='turn', y=['total_stockpile'])
            plt.show()

        # Plot a histogram of the number of children of the people who are still alive and of child-bearing age
        if self.charts['num_children_histogram']:
            children = [len(person.progeny) for person in self.people if person.alive and
                        self.params['min_reproduce_age'] <= person.age <= self.params['max_reproduce_age']]
            plt.hist(children, bins=range(0, 10))
            plt.title('Number of children')
            plt.show()

        # Plot a histogram of the ages of the people who are still alive
        if self.charts['ages_histogram']:
            ages = [person.age for person in self.people if person.alive]
            plt.hist(ages, bins=range(0, 100, 5))
            plt.title('Alive ages')
            plt.show()

        # Plot a histogram of stockpile sizes of the people who are still alive
        if self.charts['stockpile_sizes_histogram']:
            stockpiles = [person.stockpile for person in self.people if person.alive]
            if len(stockpiles) > 0:
                max_stockpile = max(stockpiles)
                plt.hist(stockpiles, bins=range(0, int(max_stockpile) + 1, 5))
                plt.title('Stockpile sizes')
                plt.show()

        # Plot a histogram of the number of relationships of living people
        if self.charts['relationship_counts']:
            relationships = [len(person.relationships) for person in self.people if person.alive]
            plt.hist(relationships, bins=range(0, 10))
            plt.title('Number of relationships')
            plt.show()

        if self.charts['relationship_strengths']:
            # Get the mean strength of a relationship and its inverse relationship
            strengths = []
            for person in [p for p in self.people if p.alive]:
                for relationship in person.relationships:
                    strengths.append(relationship.debt)
                    inverse_relationship = relationship.relationship_collection.get(relationship.person2.name,
                                                                                    relationship.person1.name)
                    if inverse_relationship:
                        strengths.append(0.5 * (relationship.debt + inverse_relationship.debt))

            # Plot a histogram of the mean strength of a relationship and its inverse relationship
            plt.hist(strengths, bins=10)
            plt.title('Mean relationship strengths')
            plt.show()

        # Plot a correlation between the number of children and the stockpile size
        if self.charts['num_children_by_stockpile']:
            children = [len(person.progeny) for person in self.people if person.alive]
            stockpiles = [person.stockpile for person in self.people if person.alive]
            plt.scatter(children, stockpiles)
            plt.xlabel('Number of children')
            plt.ylabel('Stockpile size')
            plt.title('Correlation between number of children and stockpile size')
            plt.show()

        # Display a line chart of the values of needs_met_from_resources, needs_met_from_stockpile,
        # and needs_met_from_relationships
        if self.charts['needs_met_chart']:
            df.plot(x='turn', y=['pct_with_stockpile', 'needs_met_from_resources', 'needs_met_from_stockpile',
                                 'needs_met_from_relationships', 'needs_from_parent', 'needs_not_met_died'])
            plt.show()

        # Create a boxplot of "resources_available" stat for each turn where the x-axis is the turn value and the y axis is
        # the resources available
        if self.charts['resources_available']:
            # Flatten the data
            flattened_data = []
            for entry in self.stats:
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
        if self.charts['people_to_resources_ratios']:
            df.plot(x='turn', y=['ratio_of_needs_to_resources',
                                 'ratio_of_alive_people_to_resources',
                                 'ratio_of_stockpiles_to_resources'])
            plt.show()

        # List the number of distinct values of the number of children and the nuber of people with that number of children
        children_counts = {}
        for person in self.people:
            if person.alive:
                children_count = len(person.progeny)
                if children_count not in children_counts:
                    children_counts[children_count] = 0
                children_counts[children_count] += 1

        print(children_counts)

        # Get the number of relationships with history entries
        relationships = [relationship for person in self.people if person.alive for relationship in person.relationships]
        relationships_with_history = [relationship for relationship in relationships if len(relationship.history) > 0]
        print(f'Number of relationships with history: {len(relationships_with_history)}')

        # Calculate a Gini coefficient for the stockpile sizes of alive people
        stockpiles = [person.stockpile for person in self.people if person.alive]
        if len(stockpiles) > 0:
            stockpiles.sort()
            n = len(stockpiles)
            gini_numerator = 2 * sum((i + 1) * stockpiles[i] for i in range(n))
            gini_denominator = n * sum(stockpiles)
            gini = (n + 1 - (gini_numerator / gini_denominator)) / n
            print(f'Gini coefficient for stockpile sizes: {gini}')

        # Print the number of people in total
        print(f'Total number of people: {len(self.pc.people)}')
