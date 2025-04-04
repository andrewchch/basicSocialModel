import random
from person import Person
import interfaces


class Relationship(interfaces.IRelationship):
    def __init__(self, params, relationship_collection, person1: interfaces.IPerson, person2: interfaces.IPerson):
        self.person1 = person1
        self.person2 = person2
        self.params = params
        self.relationship_collection = relationship_collection
        self.debt = params['default_relationship_strength']
        self.history = []

    def __str__(self):
        return f'Relationship between {self.person1.name} and {self.person2.name}'

    def __repr__(self):
        return f'Relationship({self.person1.name}, {self.person2.name})'

    def debt_down(self):
        self.debt -= self.params['relationship_increment']
        if self.debt < 0:
            self.debt = 0
        self.history.append({'debt': self.debt})

    def debt_up(self):
        self.debt += self.params['relationship_increment']
        if self.debt > 1:
            self.debt = 1
        self.history.append({'debt': self.debt})

    def increase_debt(self):
        # Increase the debt of the first person to the second and reduce the debt in the other direction
        self.debt_up()

        # Find the inverse relationship and reduce the debt of the other
        inverse_relationship = self.relationship_collection.get(self.person2, self.person1)
        if inverse_relationship:
            inverse_relationship.debt_down()


class RelationshipCollection(interfaces.IRelationshipCollection):
    def __init__(self, params):
        self.params = params
        self._people = None
        self.relationships = {}
        self.person_collection = None

    @property
    def people(self):
        return self._people

    @people.setter
    def people(self, new_value):
        self._people = new_value

    @property
    def person_collection(self):
        return self._person_collection

    @person_collection.setter
    def person_collection(self, new_value):
        self._person_collection = new_value

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
        """Builds relationships for one person with a set of others. A person only starts building relationships when they
        are a certain minimum age, and only build relationships with people in a certain age range"""
        assert self._people is not None, 'People must be set before building relationships'
        assert person.age >= self.params['min_rel_build_age'], 'Person must be at least the minimum relationship age'
        assert self.person_collection is not None, 'Person collection must be set before building relationships'

        if len(person.relationships) >= self.params['max_relationships']:
            return

        _others = list(self.person_collection.alive_people)
        random.shuffle(_others)

        # Filter out people who are too young or too old
        threshold = self.params['rel_build_threshold_years']
        _others = [other for other in _others if person.age - threshold <= other.age <= person.age + threshold]

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



