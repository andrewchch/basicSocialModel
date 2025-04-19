import os
import tempfile

from models.parameters import Parameters
from models.person import PersonCollection
from models.resource import ResourceCollection
from models.relationship import RelationshipCollection
from models.state import State
from models.stats import Stats


def test_simulation_state_save_and_restore():
    # Initialize parameters
    params = Parameters()
    params['turns'] = 20  # Total turns for the test

    # Initialize collections
    resource_collection = ResourceCollection(params, params['start_resources'])
    relationship_collection = RelationshipCollection(params)
    person_collection = PersonCollection(params, params['start_population'], resource_collection, relationship_collection)
    RelationshipCollection.person_collection = person_collection

    # Add a stats collector
    stats_collector = Stats()

    # Initialize state
    state = State(0, params, person_collection, resource_collection, relationship_collection, stats_collector)

    # Run the simulation for 10 turns
    for turn in range(10):
        children = []
        params['turn'] = turn
        params.apply_epochs(turn)
        for person in person_collection.shuffled_alive_people:
            child = person.lives()
            if child:
                children.append(child)
        resource_collection.grow()

        # Gather stats
        stats_collector.add(turn, children, resource_collection, person_collection)

        for child in children:
            person_collection.add(child)

    # Collect some basic stats about current state
    num_alive_people = len([person for person in person_collection.people if person.alive])
    total_resources = resource_collection.total_resources()
    totals_stats = len(stats_collector.stats)

    # Save the state to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        state_file = temp_file.name
    state.save(state_file)

    # Restore the state
    restored_state = State.load(state_file)

    # Check that the restored state matches the original state
    assert restored_state.params['start_population'] == state.params['start_population']
    assert num_alive_people == len([person for person in restored_state.person_collection.people if person.alive])
    assert total_resources == restored_state.resource_collection.total_resources()
    assert totals_stats == len(restored_state.stats_collector.stats)

    # Run the simulation for another 10 turns
    for turn in range(10, 20):
        restored_state.params['turn'] = turn
        restored_state.params.apply_epochs(turn)
        for person in restored_state.person_collection.shuffled_alive_people:
            person.lives()
        restored_state.resource_collection.grow()

    # Clean up the temporary file
    os.remove(state_file)

    # Assertions (example: check the number of turns and people)
    assert restored_state.params['turn'] == 19
    assert len(restored_state.person_collection.people) > 0
