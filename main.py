import cProfile
import pstats

from tqdm import tqdm
from models.parameters import Parameters
from models.person import PersonCollection, Traits
from models.resource import ResourceCollection
from models.relationship import RelationshipCollection
from profiling.performance import analyse
from models.charts import Charts
from models.state import State
from models.stats import Stats


def main():
    # Create some parameters
    params = Parameters()

    # Create resource collection with random amounts
    resource_collection = ResourceCollection(params, params['start_resources'])

    # Create a collection of relationships between people
    relationship_collection = RelationshipCollection(params)

    # Create a collection of people of random ages
    person_collection = PersonCollection(params, resource_collection, relationship_collection)
    person_collection.initialise(params['start_population'])

    # Add the list of people to the relationship collection
    # todo: find a tidier way to create this bidrectional relationship
    RelationshipCollection.person_collection = person_collection

    # Initialise the Traits object with the parameters reference
    Traits._params = params

    # Chart the distribution of ages
    """
    ages = [person.age for person in people]
    plt.hist(ages, bins=range(0, 100, 5))
    plt.title('Ages')
    plt.show()
    """

    # Add epochs
    # params.add_epoch(Epoch(500, 2000, {'grow_chance': 0.5}))
    # params.add_epoch(Epoch(500, 2000, {'stockpiling_need_per_turn_max': 0}))
    # params.add_epoch(Epoch(500, 2000, {'find_resources_count': 2}))
    # params.add_epoch(Epoch(500, 2000, {'need_per_turn': 4}))

    # Create a stats collector
    stats_collector = Stats()

    try:
        for turn in tqdm(range(0, params['turns']), desc='Simulating', unit='turns'):
            children = []

            params['turn'] = turn

            # Update the parameters for this turn
            params.apply_epochs(turn)

            # People meet their needs and have children
            for person in person_collection.shuffled_alive_people:
                child = person.lives()
                if child:
                    children.append(child)

            # Grow the resources
            resource_collection.grow()

            # Gather stats
            if turn % 50 == 0:
                stats_collector.add(turn, children, resource_collection, person_collection)

            # Append any children to people list. We do this last because the children are not alive until the next
            # turn, and we don't want to include them in the stats
            for child in children:
                person_collection.add(child)

    except KeyboardInterrupt:
        print("\nLoop interrupted. Continuing with the rest of the program.")

    # Pickle the simulation state
    state = State(turn, params, person_collection, resource_collection, relationship_collection, stats_collector)
    state.save("simulation_state.pkl")

    # Plot the stats
    charter = Charts(stats_collector.stats, params, person_collection)
    charter.display()


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







