import random
import numpy as np
import interfaces


class Person(interfaces.IPerson):
    def __init__(self, params, name, age, resource_collection: interfaces.IResourceCollection, relationship_collection):
        self.name = name
        self.params = params
        self.age = age
        self.max_age = random.randint(params['max_age_min'], params['max_age_max'])
        self.alive = True
        self.progeny = []
        self.need_per_turn = params['need_per_turn']
        self.stockpile = 0
        self.stockpiling_need_per_turn = random.randint(params['stockpiling_need_per_turn_min'], params['stockpiling_need_per_turn_max'])
        self.max_children = random.randint(params['max_children_min'], params['max_children_max'])
        self.resource_collection = resource_collection
        self.child_chance = params['child_chance']
        self.relationships = []
        self.relationship_collection = relationship_collection

        if self.relationship_collection and self.relationship_collection.people:
            self.build_relationships()

    def __str__(self):
        return f'Person {self.name} is {self.age} years old'

    def __repr__(self):
        return f'Person({self.name}, {self.age})'

    def build_relationships(self):
        # Build a set of relationships
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

        child_name = '%s_c%s' % (self.name, len(self.progeny) + 1)

        child = Person(self.params, child_name, 0, self.resource_collection, self.relationship_collection)
        self.progeny.append(child)
        return child

    def die(self):
        self.alive = False

    def meet_needs(self):
        """Meet our needs by consuming resources"""
        needs = self.need_per_turn
        stockpile_needs = self.stockpiling_need_per_turn

        # Find a set of resources that can meet our needs (and our desire to stockpile)
        resources = self.resource_collection.find_resources()
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

        # If we can't find enough resources to meet our needs, consume our stockpile
        if needs > 0:
            needs_from_stockpile = min(needs, self.stockpile)
            self.stockpile -= needs_from_stockpile
            needs -= needs_from_stockpile

        # If we don't have enough in our stockpile, ask one of our related people for help
        if needs > 0:
            for relationship in self.relationships:
                # If this relationship is too weak, skip it
                if relationship.strength < self.params['relationship_threshold']:
                    continue

                if needs <= 0:
                    break
                other = relationship.person2
                if other.stockpile > 0:
                    needs_from_other = min(needs, other.stockpile)
                    other.stockpile -= needs_from_other
                    needs -= needs_from_other

                    # Update the strength of both of our relationships
                    relationship.update()

        # If we still can't meet our needs, we die
        if needs > 0:
            # Divide our stockpile equally between our children
            if len(self.progeny) > 0:
                stockpile_per_child = self.stockpile // len(self.progeny)
                for child in self.progeny:
                    child.stockpile += stockpile_per_child
                self.stockpile = 0

            self.die()

    def ages(self):
        """Ages the person by one year"""
        self.age += 1
        if self.age > self.max_age:
            self.die()

    def lives(self):
        """A person lives for a turn"""
        if not self.alive:
            return

        self.meet_needs()

        child = self.have_child()

        self.ages()

        return child


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

        self.people = [Person(params, 'p%s' % i, numbers[i], resource_collection, relationship_collection) for i in range(count)]

    def add(self, person):
        self.people.append(person)
