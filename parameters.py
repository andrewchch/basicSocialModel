from epoch import Epoch
from copy import copy


class Parameters:
    """
    Holds a set of default parameters for the run of the simulation, and applies epochs where
    the parameters change.
    """

    def __init__(self):
        self._params = {
            'turn': 0,
            'start_population': 500,
            'start_resources': 2000,
            'turns': 2000,
            'age_std_dev': 15,
            'age_mean': 40,
            'max_age': 80,
            'max_age_min': 60,
            'max_age_max': 80,
            'child_chance': 0.07,
            'max_children_min': 1,
            'max_children_max': 3,
            'need_per_turn': 2,
            'stockpiling_need_per_turn_min': 0.1,
            'stockpiling_need_per_turn_max': 0.5,
            'min_reproduce_age': 18,
            'max_reproduce_age': 40,
            'resource_max_amount': 2,
            'find_resources_count': 5,
            'grow_amount': 1,
            'grow_chance': 1.0,
            'max_relationships': 5,
            'default_relationship_strength': 0.5,
            'relationship_increment': 0.1,
            'max_debt': 0.7,
            'min_rel_build_age': 16,
            'rel_build_threshold_years': 5,
            'min_self_sufficient_age': 7,
            'min_stockpile_for_breeding': 3,
        }
        self.params = copy(self._params)
        self.epochs = []
        self._turn = 0

    def __setitem__(self, key, value):
        self.params[key] = value

    def __getitem__(self, item):
        return self.params[item]

    def add_epoch(self, epoch: Epoch):
        self.epochs.append(epoch)

    def remove_epoch(self, epoch: Epoch):
        self.epochs.remove(epoch)

    def apply_epochs(self, turn):
        """
        Apply the parameters for the given turn, only once per turn
        """
        if turn != self._turn:
            for epoch in self.epochs:
                if epoch.start <= turn <= epoch.end:
                    self.params.update(epoch.params)
                else:
                    # Outside the epoch, reset the parameters to the default
                    for key in epoch.params:
                        if key in self.params:
                            self.params[key] = self._params[key]
            self._turn = turn

    def __getitem__(self, item):
        return self.params[item]

