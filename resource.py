import random
import interfaces


class Resource(interfaces.IResource):
    def __init__(self, params):
        self.params = params
        self.amount = self.params['resource_max_amount']

    def __str__(self):
        return f'{self.amount}'

    def __repr__(self):
        return f'Resource({self.amount})'

    def consumed(self, amount):
        """something consumes an amount of this resource"""
        returned_amount = min(self.amount, amount)
        self.amount -= returned_amount
        return returned_amount

    def produce(self, amount):
        """An amount of this resource is produced"""
        self.amount += amount
        if self.amount > self.params['resource_max_amount']:
            self.amount = self.params['resource_max_amount']


class ResourceCollection(interfaces.IResourceCollection):
    def __init__(self, params, count=100):
        self.params = params
        self.resources = [Resource(params) for i in range(0, count)]

    def find_resources(self, count=5):
        """ return a random set of N resource"""
        return random.sample(self.resources, self.params['find_resources_count'])

    def grow(self):
        for resource in self.resources:
            resource.produce(self.params['grow_amount'])

    def total_resources(self):
        return sum([resource.amount for resource in self.resources])



