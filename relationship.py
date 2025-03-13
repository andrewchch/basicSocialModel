import random
from person import Person
import interfaces


class Relationship(interfaces.IRelationship):
    def __init__(self, params, relationship_collection, person1: interfaces.IPerson, person2: interfaces.IPerson):
        self.person1 = person1
        self.person2 = person2
        self.params = params
        self.relationship_collection = relationship_collection
        self.strength = params['default_relationship_strength']

    def __str__(self):
        return f'Relationship between {self.person1.name} and {self.person2.name}'

    def __repr__(self):
        return f'Relationship({self.person1.name}, {self.person2.name})'

    def weaken(self):
        self.strength -= self.params['relationship_increment']
        if self.strength < 0:
            self.strength = 0

    def strengthen(self):
        self.strength += self.params['relationship_increment']
        if self.strength > 1:
            self.strength = 1

    def update(self):
        # Increment the strength of the relationship from person1 to person2
        self.strengthen()

        # Find the inverse relationship and decrement its strength
        inverse_relationship = self.relationship_collection.get(self.person2, self.person1)
        if inverse_relationship:
            inverse_relationship.weaken()
        else:
            pass


class RelationshipCollection(interfaces.IRelationshipCollection):
    def __init__(self, params):
        self.params = params
        self._people = None
        self.relationships = {}

    @property
    def people(self):
        return self._people

    @people.setter
    def people(self, new_value):
        self._people = new_value

    def add(self, person1, person2):
        """Add a relationship between two people, but return None if the relationship already exists"""
        if (person1.name, person2.name) in self.relationships:
            return None
        relationship = Relationship(self.params, self, person1, person2)
        self.relationships[(person1.name, person2.name)] = relationship
        return relationship

    def get(self, person1: Person, person2: Person):
        return self.relationships.get((person1.name, person2.name), None)

    def build_relationships(self, person: Person):
        """Builds relationships for one person with a set of others"""
        assert self._people is not None, 'People must be set before building relationships'

        if len(person.relationships) >= self.params['max_relationships']:
            return

        _others = list(self._people)
        random.shuffle(_others)

        found = False

        for _other in _others:
            if _other == person:
                continue
            for relationship in person.relationships:
                if relationship.person2 == _other:
                    found = True
                    break
            if not found:
                # Create the forward and reverse relationships
                relationship = self.add(person, _other)
                if relationship:
                    person.relationships.append(relationship)

                relationship = self.add(_other, person)
                if relationship:
                    _other.relationships.append(relationship)
            if len(person.relationships) >= self.params['max_relationships']:
                break



