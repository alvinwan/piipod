from .csp import SignupCSP
from .sma import SignupSMA

class Resolver(object):
    """Resolver object for processing waitlist or importing signups"""

    __solvers = {
        'CSP': SignupCSP,
        'SMA': SignupSMA
    }

    solver = None

    def __init__(self, solver):
        """set solver based on string"""
        self.solver = self.__solvers[solver]()

    
