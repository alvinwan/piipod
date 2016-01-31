from random import random
from constraint import *


class SignupCSP(object):
    """

    Signups CSP
    ---

    Signups CSP is an event signups constraint satisfaction problem, abstracted
    for easier use. The original constraints object can be accessed directly.

    This CSP class accepts two forms of input:
    - events tag, where each event associated with the tag has a waitlist
    - list of events, where each event has a waitlist
    - list of event details and user emails

    Currently supports the following constraints:
    - per-event signup maximum and minimum
    - per-user signup maximum and minimum
    """

    def __init__(user_ids, event_ids):
        """Accepts iterables of user ids and event ids"""


    @staticmethod
    def random_variable(length=5):
        """
        >>> f = SignupCSP.random_variable
        >>> len(f(3)) == 3
        True
        >>> f(3) != f(3)
        True
        """
        string = ''
        for _ in range(length):
            string += chr(int(random()*27))
        return string


if __name__ == '__main__':
    import doctest
    doctest.testmod()
