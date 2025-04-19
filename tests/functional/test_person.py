from models.person import Person, PersonCollection
from models.relationship import RelationshipCollection
from models.resource import ResourceCollection
from models.parameters import Parameters


def test_ask_for_resources():
    params = Parameters()
    resource_collection = ResourceCollection(params)
    relationship_collection = RelationshipCollection(params)
    person_collection = PersonCollection(params, resource_collection, relationship_collection)
    RelationshipCollection.person_collection = person_collection

    # Create two people with different stockpiles
    person1 = Person(params, 30, resource_collection, relationship_collection,
                 person_collection, None)
    person1.need_per_turn = 2
    person_collection.add(person1)

    person2 = Person(params, 25, resource_collection, relationship_collection,
                    person_collection, None)
    person2.need_per_turn = 2
    person_collection.add(person2)

    # Person1 has one child (just create the child Person and manually add it to progeny)
    child = Person(params, 5, resource_collection, relationship_collection,
                   person_collection, person1)
    person1.progeny.append(child)

    # Initialise the stockpiles
    person1.stockpile = 5
    person2.stockpile = 10

    # Person 1 asks Person 2 for if they have resources to give
    val = person2.resources_available_to_give(2, person1)
    assert val == 2  # Person 2 can give 2 resources
    assert person2.stockpile == 10  # Person 2's stockpile should remain unchanged

    # Person 1 asks Person 2 for the resources
    val = person2.provide_resources(2, person1)
    assert val == 2  # Person 2 gives 2 resources
    assert person2.stockpile == 8  # Person 2's stockpile is reduced

    # Person 1 asks Person 2 for the 1 resource
    val = person2.provide_resources(1, person1)
    assert val == 1  # Person 2 gives 1 resource
    assert person2.stockpile == 7 # Person 2's stockpile is reduced
