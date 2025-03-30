import random
import numpy as np
import interfaces
import uuid


class ResourcesMetEnum:
    FROM_RESOURCES = 1
    FROM_STOCKPILE = 2
    FROM_RELATIONSHIPS = 3
    NOT_MET_DIED = 4


class HowDiedEnum:
    STARVED = 1
    OLD_AGE = 2


class Person(interfaces.IPerson):
    def __init__(self, params, age, resource_collection: interfaces.IResourceCollection, relationship_collection,
                 person_collection: interfaces.IPersonCollection):
        self.born = params['turn']
        self.died = None
        self.how_died = None
        self.name = uuid.uuid4()
        self.params = params
        self.age = age
        self.max_age = random.randint(params['max_age_min'], params['max_age_max'])
        self.alive = True
        self.progeny = []
        self.need_per_turn = params['need_per_turn']
        self.stockpile = 0
        self.max_children = random.randint(params['max_children_min'], params['max_children_max'])
        self.resource_collection = resource_collection
        self.child_chance = params['child_chance']
        self.relationships = []
        self.relationship_collection = relationship_collection
        self.needs_met = 0
        self.resources_available = None
        self.stats = []
        self.parent = None
        self.person_collection = person_collection

        # Initialise the stockpiling need
        min_spnt = params['stockpiling_need_per_turn_min']
        max_spnt = params['stockpiling_need_per_turn_max']
        self.stockpiling_need_per_turn = random.random() * (max_spnt - min_spnt) + min_spnt

    def __str__(self):
        return f'Person {self.name} is {self.age} years old'

    def __repr__(self):
        return f'Person({self.name}, {self.age})'

    def build_relationships(self):
        # Build a set of relationships if we don't have the maximum number of relationships
        self.relationship_collection.build_relationships(self)

    def have_child(self):
        if not self.alive:
            return None

        if self.age < self.params['min_reproduce_age'] or self.age > self.params['max_reproduce_age']:
            return None

        if random.random() > self.child_chance:
            return

        if len(self.progeny) >= self.max_children:
            return

        if self.stockpile < self.params['min_stockpile_for_breeding']:
            return

        child = Person(self.params, 0, self.resource_collection, self.relationship_collection,
                       self.person_collection)
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
        self.alive = False
        self.died = self.params['turn']
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
        self.person_collection.decease(self)

    def meet_needs(self):
        """Meet our needs by consuming resources"""
        needs = self.need_per_turn
        stockpile_needs = self.stockpiling_need_per_turn

        # If we are less than a certain age, we can only have our needs met from our parent's stockpile
        if self.age < self.params['min_self_sufficient_age']:
            if self.parent:
                needs_from_parent = self.parent.contribute(needs)
                needs -= needs_from_parent

                # If we can't get enough from our parent, we die
                if needs > 0:
                    self.needs_met = ResourcesMetEnum.NOT_MET_DIED
                    self.die(HowDiedEnum.STARVED)
                    return

        # Find a set of resources that can meet our needs (and our desire to stockpile)
        resources = self.resource_collection.find_resources()
        self.resources_available = sum([resource.amount for resource in resources])

        for resource in resources:
            if needs > 0:
                consumed = resource.consumed(needs)
                needs -= min(consumed, needs)
            elif stockpile_needs > 0:
                consumed = resource.consumed(stockpile_needs)
                self.stockpile += consumed
                stockpile_needs -= consumed
                if stockpile_needs <= 0:
                    break
            else:
                break

        if needs <= 0:
            self.needs_met = ResourcesMetEnum.FROM_RESOURCES
            return

        # If we can't find enough resources to meet our needs, consume our stockpile
        needs_from_stockpile = min(needs, self.stockpile)
        self.stockpile -= needs_from_stockpile
        needs -= needs_from_stockpile

        if needs <= 0:
            self.needs_met = ResourcesMetEnum.FROM_STOCKPILE
            return

        # If we don't have enough in our stockpile, ask one of our related people for help
        for relationship in self.relationships:
            # If we are more than a certain amount in debt, we can't ask for help
            if relationship.debt > self.params['max_debt']:
                continue

            if needs <= 0:
                break
            other = relationship.person2
            if other.stockpile > 0:
                needs_from_other = min(needs, other.stockpile)
                other.stockpile -= needs_from_other
                needs -= needs_from_other

                # Since I got something from them, my "credit" is lowered and theirs is raised
                relationship.increase_debt()

        if needs <= 0:
            self.needs_met = ResourcesMetEnum.FROM_RELATIONSHIPS
            return

        # If we still can't meet our needs, we die
        self.needs_met = ResourcesMetEnum.NOT_MET_DIED
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

        # Meet needs
        self.meet_needs()

        # Have a child
        child = self.have_child()

        # Build relationships
        if self.age > self.params['min_rel_build_age']:
            if self.relationship_collection and self.relationship_collection.people:
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

        self.people = [Person(params, numbers[i], resource_collection, relationship_collection, self) for i in range(count)]

        # We'll keep a dictionary of alive people for efficient lookup
        self._alive_people = {person.name: person for person in self.people}

    def add(self, person):
        self.people.append(person)
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
