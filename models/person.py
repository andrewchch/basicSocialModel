import random
import numpy as np
import uuid
from copy import copy

from models import interfaces


class ResourcesMetEnum:
    FROM_RESOURCES = 1
    FROM_STOCKPILE = 2
    FROM_RELATIONSHIPS = 3
    FROM_PARENT = 4
    NOT_MET_DIED = 5


class StockpileNeedsMetEnum:
    FROM_RESOURCES = 1
    FROM_RELATIONSHIPS = 2
    NOT_MET = 3
    NO_NEEDS = 4


class HowDiedEnum:
    STARVED = 1
    OLD_AGE = 2


class Traits:
    _params = None

    def __init__(self, params=None):
        if Traits._params is None and params is not None:
            Traits._params = params
        self._traits = {}

    def add(self, trait, value):
        self._traits[trait] = value

    def __getitem__(self, trait):
        if trait in self._traits:
            return self._traits[trait]

        if trait in Traits._params:
            return Traits._params[trait]

        return None

    def __setitem__(self, trait, value):
        self._traits[trait] = value

    def __iter__(self):
        return iter(self._traits)

    def __contains__(self, item):
        return item in self._traits


class Person(interfaces.IPerson):
    _params = None
    person_collection = None
    resource_collection = None
    relationship_collection = None
    
    def __init__(self, params, age, resource_collection: interfaces.IResourceCollection, relationship_collection,
                 person_collection: interfaces.IPersonCollection, parent: interfaces.IPerson):
        self.born = params['turn']
        self.died = None
        self.how_died = None
        self.name = str(uuid.uuid4())
        self.age = age
        self.max_age = random.randint(params['max_age_min'], params['max_age_max'])
        self.alive = True
        self.need_per_turn = params['need_per_turn']
        self.stockpile = 0
        self.needs_met = None
        self.stockpile_needs_met = None
        self.resources_available = None
        self.stats = []
        self.need_from_parent = params['need_per_turn']  # When we are born we depend on our parents
        self.relationships = []

        # If we're already older than our max age, set our max age to our current age + 1
        if self.age > self.max_age:
            self.max_age = self.age + 1

        # Initialise the stockpiling need
        min_spnt = params['stockpiling_need_per_turn_min']
        max_spnt = params['stockpiling_need_per_turn_max']
        self.stockpiling_need_per_turn = random.random() * (max_spnt - min_spnt) + min_spnt

        # Things we will need to restore on deserialization
        self._params = params
        self.parent = parent
        self.progeny = []
        
        if Person.person_collection is None and person_collection is not None:
            Person.person_collection = person_collection
            
        if Person.resource_collection is None and resource_collection is not None:
            Person.resource_collection = resource_collection
            
        if Person.relationship_collection is None and relationship_collection is not None:
            Person.relationship_collection = relationship_collection

        # Initialise our default traits
        self.traits = Traits(params)
        self.traits.add('child_chance', random.random())
        self.traits.add('min_stockpile_for_breeding', random.randrange(10, 25))

        # Update our traits from our parent but mutate them slightly
        if parent:
            for trait in parent.traits:
                self.traits[trait] = parent.traits[trait]
                self.traits[trait] *= (random.random() < 0.5 and 0.9 or 1.1)

    def __str__(self):
        return f'Person {self.name} is {self.age} years old'

    def __repr__(self):
        return f'Person({self.name}, {self.age})'

    def __getstate__(self):
        state = self.__dict__.copy()

        # Replace references to parent and children with their names
        if self.parent:
            state['parent'] = self.parent.name

        state['progeny'] = [child.name for child in self.progeny]
        state['relationships'] = [relationship.person2.name for relationship in self.relationships]
        return state

    def __setstate__(self, state):
        # Restore the state
        self.__dict__.update(state)

        # Restore the parent and progeny
        if 'parent' in state and state['parent'] is not None:
            self.parent = Person.person_collection[state['parent']]
        else:
            self.parent = None

        if 'progeny' in state:
            self.progeny = [Person.person_collection[child_name] for child_name in state['progeny']]
        else:
            self.progeny = []

        if 'relationships' in state:
            self.relationships = [Person.relationship_collection.get(self.name, relationship_name)
                                  for relationship_name in state['relationships']]
        else:
            self.relationships = []

    def build_relationships(self):
        # Build a set of relationships if we don't have the maximum number of relationships
        Person.relationship_collection.build_relationships(self)

    def have_child(self):
        if not self.alive:
            return None

        if self.age < self.traits['min_reproduce_age'] or self.age > self.traits['max_reproduce_age']:
            return None

        if random.random() > self.traits['child_chance']:
            return

        if self.stockpile < self.traits['min_stockpile_for_breeding']:
            return

        # Create a child and return it
        child = self.add_child()
        return child

    def add_child(self):
        """Add a child to this person"""
        child = Person(self._params, 0, self.resource_collection, self.relationship_collection,
                       Person.person_collection, self)
        self.progeny.append(child)
        return child

    def contribute(self, amount):
        """Contribute an amount of resources to someone else"""
        if amount <= 0:
            return 0

        if self.stockpile >= amount:
            self.stockpile -= amount
            return amount

        amount_from_stockpile = self.stockpile
        self.stockpile = 0
        return amount_from_stockpile

    def die(self, how_died):
        if not self.alive:
            return

        self.alive = False
        self.died = self._params['turn']
        self.how_died = how_died

        # Divide our stockpile equally between our alive children
        # todo: find an inexpensive way to allocate all of the stockpile to alive ancestors
        alive_children = [child for child in self.progeny if child.alive]
        if len(alive_children) > 0:
            stockpile_per_child = self.stockpile // len(alive_children)
            for child in alive_children:
                child.stockpile += stockpile_per_child
            self.stockpile = 0

        # Ask our person collection to remove us
        Person.person_collection.decease(self)

    def meet_needs(self):
        """Meet our needs by consuming resources"""
        needs = self.need_per_turn

        # Our stockpile needs are our own plus our children's
        children_needs = sum([child.need_from_parent for child in self.progeny if child.alive])
        stockpile_needs = self.stockpiling_need_per_turn + children_needs
        from_stockpile = True

        # If we are less than a certain age, we can have our needs met from our parent's stockpile or our stockpile
        if self.age < self.traits['min_self_sufficient_age']:
            from_parent = True
            from_resources = False
            from_relationships = False
            self.stockpile_needs_met = StockpileNeedsMetEnum.NO_NEEDS
        else:
            from_parent = False
            from_resources = True
            from_relationships = True

        # Get resources from the parent
        if from_parent:
            if self.parent and self.parent.alive:
                needs_from_parent = self.parent.contribute(needs)
                needs -= needs_from_parent

            if needs <= 0:
                self.needs_met = ResourcesMetEnum.FROM_PARENT
                self.stockpile_needs_met = StockpileNeedsMetEnum.NO_NEEDS
                return

        # Find a set of resources that can meet our needs (and our desire to stockpile)
        if from_resources:
            resources = self.resource_collection.find_resources()
            self.resources_available = sum([resource.amount for resource in resources])

            for resource in resources:
                if needs > 0:
                    consumed = resource.consumed(needs)
                    needs -= min(consumed, needs)
                elif stockpile_needs > 0:
                    consumed = resource.consumed(stockpile_needs)
                    self.stockpile += consumed
                    stockpile_needs -= min(consumed, stockpile_needs)

                # If we have met our needs, we can stop looking for resources
                if needs <= 0 and stockpile_needs <= 0:
                    break

            if needs <= 0:
                self.needs_met = ResourcesMetEnum.FROM_RESOURCES

            if stockpile_needs <= 0:
                self.stockpile_needs_met = StockpileNeedsMetEnum.FROM_RESOURCES

        # If we can't find enough resources to meet our needs, consume our stockpile
        if from_stockpile and needs > 0:
            needs_from_stockpile = min(needs, self.stockpile)
            self.stockpile -= needs_from_stockpile
            needs -= needs_from_stockpile

            if needs <= 0:
                self.needs_met = ResourcesMetEnum.FROM_STOCKPILE

        # If we haven't met our needs or don't have enough in our stockpile, ask one of our related people for help
        if from_relationships and (needs > 0 or stockpile_needs > 0):
            # Meet our personal needs first
            for relationship in self.relationships:
                # If we are more than a certain amount in debt, we can't ask for help
                if relationship.debt > self.traits['max_debt']:
                    continue

                other = relationship.person2
                resources_from_other = 0

                if other.stockpile > 0:
                    if needs > 0:
                        resources_from_other = min(needs, other.stockpile)
                        other.stockpile -= resources_from_other
                        needs -= resources_from_other
                    elif stockpile_needs > 0:
                        resources_from_other = min(self.traits['max_stockpile_transfer'], other.stockpile)
                        self.stockpile += resources_from_other
                        other.stockpile -= resources_from_other
                        stockpile_needs -= resources_from_other

                    # Since I got something from them, my "credit" is lowered and theirs is raised
                    if resources_from_other > 0:
                        relationship.increase_debt()

                if needs <= 0 and stockpile_needs <= 0:
                    break

            if needs <= 0:
                self.needs_met = ResourcesMetEnum.FROM_RELATIONSHIPS

            if stockpile_needs <= 0:
                self.stockpile_needs_met = StockpileNeedsMetEnum.FROM_RELATIONSHIPS

        # If we've met our basic needs we can stop
        if needs <= 0:
            return

        # If we still can't meet our needs, we die
        self.needs_met = ResourcesMetEnum.NOT_MET_DIED
        self.stockpile_needs_met = StockpileNeedsMetEnum.NOT_MET

        self.die(HowDiedEnum.STARVED)

    def ages(self):
        """Ages the person by one year"""
        self.age += 1
        if self.age > self.max_age:
            self.die(HowDiedEnum.OLD_AGE)

    def lives(self):
        """A person lives for a turn"""
        if not self.alive:
            return

        # Adjust our needs from our parent
        if self.age >= self.traits['min_self_sufficient_age']:
            self.need_from_parent = 0

        # Meet needs
        self.meet_needs()

        # If we are dead, we can't do anything else
        if not self.alive:
            return

        # Have a child
        child = self.have_child()

        # Build relationships
        if self.age > self.traits['min_rel_build_age']:
            if self.relationship_collection:
                self.build_relationships()

        # Age the person
        self.ages()

        # Gather stats
        self.gather_stats()

        return child

    def gather_stats(self):
        self.stats.append({
            'age': self.age,
            'progeny': len(self.progeny),
            'stockpile': self.stockpile,
            'relationships': len(self.relationships),
            'needs_met': self.needs_met,
            'resources_available': self.resources_available
        })


class PersonCollection:
    def __init__(self, params, count, resource_collection, relationship_collection):
        # Parameters for the Gaussian distribution
        mean = params['age_mean']
        std_dev = params['age_std_dev']
        size = count

        # Generate the numbers
        numbers = np.random.normal(mean, std_dev, size)

        # Clip the values to be between 1 and max_age
        numbers = np.clip(numbers, 1, params['max_age'])

        people = [Person(params, numbers[i], resource_collection, relationship_collection, self, None) for i in range(count)]

        # We'll keep dictionaries of all people and alive people for efficient lookup and deserialisation
        self._alive_people = {person.name: person for person in people}
        self._people = copy(self._alive_people)

    @property
    def people(self):
        return self._people.values()

    def add(self, person):
        self._people[person.name] = person
        self._alive_people[person.name] = person

    def decease(self, person):
        # We don't remove the person, just remove them from the alive list
        del self._alive_people[person.name]

    @property
    def shuffled_alive_people(self):
        keys = list(self._alive_people.keys())
        random.shuffle(keys)
        for key in keys:
            yield self._alive_people[key]

    @property
    def alive_people(self):
        for person in self._alive_people.values():
            yield person

    def __getitem__(self, key):
        return self._people[key]

