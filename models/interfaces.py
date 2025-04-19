class IResource:

    def consumed(self, amount):
        pass

    def produce(self, amount):
        pass


class IResourceCollection:
    def find_resources(self, count=5):
        pass

    def grow(self):
        pass

    def total_resources(self):
        pass


class IPerson:
    def __init__(self, params, name, age, resource_collection: IResourceCollection, relationship_collection):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass

    def have_child(self):
        pass

    def die(self):
        pass

    def meet_needs(self):
        pass

    def ages(self):
        pass

    def lives(self):
        pass


class IPersonCollection:
    def add(self, person: IPerson):
        pass


class IRelationship:
    def __init__(self, params, person1: IPerson, person2: IPerson):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass

    def weaken(self):
        pass

    def strengthen(self):
        pass


class IRelationshipCollection:
    def add(self, person1: IPerson, person2: IPerson):
        pass

    def get(self, person1: IPerson, person2: IPerson):
        pass

    def build_relationships(self, person: IPerson):
        pass

    def update(self, relationship: IRelationship):
        pass




