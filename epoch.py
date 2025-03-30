class Epoch:
    """
    An epoch is a range of turns in which a set of parameters change value. The value can either be static or a function
    of the turn number. After the epoch ends, the parameters are reverted to their previous values.
    """

    def __init__(self, start, end, params):
        self.start = start
        self.end = end
        self.params = params