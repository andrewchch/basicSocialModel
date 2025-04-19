import pickle

from models.person import Person, Traits
from models.relationship import RelationshipCollection


class State:
    """
    A class for marshalling and unmarshalling the state of the simulation.
    """
    def __init__(self, turn, params, person_collection, resource_collection, relationship_collection, stats_collector):
        self.turn = turn
        self.params = params
        self.person_collection = person_collection
        self.resource_collection = resource_collection
        self.relationship_collection = relationship_collection
        self.stats_collector = stats_collector

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.__dict__, f)

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            import pickle
            state_dict = pickle.load(f)

        # Restore params
        params = state_dict.get('params')

        # Restore the resource collection
        resource_collection = state_dict.get('resource_collection')
        resource_collection._params = params

        # Restore the person collection
        person_collection = state_dict.get('person_collection')
        Traits._params = params
        Person._params = params
        Person.resource_collection = resource_collection
        Person.person_collection = person_collection

        # Restore the relationship collection
        relationship_collection = state_dict.get('relationship_collection')
        relationship_collection._params = params
        RelationshipCollection.person_collection = person_collection
        Person.relationship_collection = relationship_collection

        return cls(**state_dict)

