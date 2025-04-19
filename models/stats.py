from models.person import ResourcesMetEnum, HowDiedEnum


def get_filter_length(lmb, a):
    return sum(1 for _ in (filter(lmb, a)))


def gather_stats(turn, children, resource_collection, person_collection):
    alive_people = [p for p in person_collection.alive_people]
    num_alive_people = len(alive_people)

    if num_alive_people == 0:
        return

    # Get the number of people alive in this turn and the number of people who have died
    died_this_turn = list(filter(lambda p: p.died == turn, person_collection.people))
    num_people_acted_in_turn = num_alive_people + len(died_this_turn)
    num_people = len(person_collection.people)

    # Stats for percentages of people having their needs met from different sources
    needs_met_from_resources = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_RESOURCES,
                                                 alive_people) / num_people_acted_in_turn
    needs_met_from_stockpile = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_STOCKPILE,
                                                 alive_people) / num_people_acted_in_turn
    needs_met_from_relationships = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_RELATIONSHIPS,
                                                     alive_people) / num_people_acted_in_turn
    needs_from_parent = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.FROM_PARENT,
                                          alive_people) / num_people_acted_in_turn
    needs_not_met_died = get_filter_length(lambda p: p.needs_met == ResourcesMetEnum.NOT_MET_DIED,
                                           died_this_turn) / num_people_acted_in_turn

    # Get counts of how people died in this turn
    num_starved = get_filter_length(lambda p: p.how_died == HowDiedEnum.STARVED, died_this_turn)
    num_old_age = get_filter_length(lambda p: p.how_died == HowDiedEnum.OLD_AGE, died_this_turn)

    # Calculate the total of all stockpiles of alive people plus all resources
    total_stockpile = sum([person.stockpile for person in alive_people])
    total_resources = resource_collection.total_resources()
    total_stockpile_and_resources = total_stockpile + total_resources

    # Collect stats
    return {
        'turn': turn,
        'people': num_people,
        'alive': num_alive_people,
        'dead': num_people - num_alive_people,
        'average_age_of_death': sum([person.age for person in died_this_turn]) / len(died_this_turn) if len(
            died_this_turn) > 0 else 0,
        'resources': resource_collection.total_resources(),
        'average_number_of_children': sum([len(person.progeny) for person in alive_people]) / num_alive_people,
        'average_age': sum([person.age for person in alive_people]) / num_alive_people,
        'children_born_per_year': len(children),
        'average_stockpile': sum([person.stockpile for person in alive_people]) / num_alive_people,
        'total_stockpile': sum([person.stockpile for person in alive_people]),
        'pct_with_stockpile': get_filter_length(lambda p: p.stockpile > 0, alive_people) / num_alive_people,
        'total_stockpile_need_per_turn': sum([person.stockpiling_need_per_turn for person in alive_people]),
        'total_children_with_alive_parents': sum([len(person.progeny) for person in alive_people]),
        'needs_met_from_resources': needs_met_from_resources,
        'needs_met_from_stockpile': needs_met_from_stockpile,
        'needs_met_from_relationships': needs_met_from_relationships,
        'needs_from_parent': needs_from_parent,
        'needs_not_met_died': needs_not_met_died,
        'resources_available': [person.resources_available for person in alive_people if
                                person.needs_met == ResourcesMetEnum.NOT_MET_DIED and person.died == turn],
        'num_starved': num_starved,
        'num_old_age': num_old_age,
        'ratio_of_needs_to_resources': sum(
            [person.need_per_turn for person in alive_people]) / total_stockpile_and_resources,
        'ratio_of_alive_people_to_resources': num_alive_people / total_stockpile_and_resources,
        'ratio_of_stockpiles_to_resources': total_stockpile / total_resources,
        'average_child_chance': sum([person.traits['child_chance'] for person in alive_people]) / num_alive_people,
        'min_stockpile_for_breeding_avg': sum(
            [person.traits['min_stockpile_for_breeding'] for person in alive_people]) / num_alive_people,
        'min_stockpile_for_breeding': [person.traits['min_stockpile_for_breeding'] for person in alive_people],
        'died_this_turn_ages': [person.age for person in died_this_turn],
    }

    return stat


class Stats:

    def __init__(self):
        self._stats = []

    def add(self, turn, children, resource_collection, person_collection):
        stat = gather_stats(turn, children, resource_collection, person_collection)
        self._stats.append(stat)
        return stat

    @property
    def stats(self):
        return self._stats


