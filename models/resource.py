import random
from models import interfaces


class Resource(interfaces.IResource):
    _params = None

    def __init__(self, params=None):
        if Resource._params is None and params is not None:
            Resource._params = params
        self.amount = self.params['resource_max_amount']

    @property
    def params(self):
        return Resource._params

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
    _params = None

    def __init__(self, params, count=100):
        if ResourceCollection._params is None and params is not None:
            ResourceCollection._params = params
        self.resources = [Resource(params) for i in range(0, count)]

    @property
    def params(self):
        return ResourceCollection._params

    def find_resources(self, count=0):
        """ return a random set of N resource"""
        _count = count > 0 and count or self.params['find_resources_count']
        return random.sample(self.resources, _count)

    def grow(self):
        for resource in self.resources:
            if random.random() < self.params['grow_chance']:
                resource.produce(self.params['grow_amount'])

    def total_resources(self):
        return sum([resource.amount for resource in self.resources])



