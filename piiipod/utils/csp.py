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

    def __init__(self, user_ids, event_ids):
        """Accepts iterables of user ids and event ids"""
        self.problem = Problem()

        for uid in user_ids:
            self.addVariable(uid, list(range(len(event_ids)+1)))
            signups = ['%s__%s' % (str(uid), str(eid)) for eid in event_ids]
            for signup in signups:
                self.addVariable(signup, [0, 1])
            self.addConstraint(
                lambda *args: args[-1] == sum(args[:-1]), signups + [uid])

        for eid in event_ids:
            self.addVariable(eid, list(range(len(user_ids)+1)))
            signups = ['%s__%s' % (str(uid), str(eid)) for uid in user_ids]
            self.addConstraint(
                lambda *args: args[-1] == sum(args[:-1]), signups + [eid])

    def addVariable(self, variable, domain):
        """Add a variable to the problem"""
        self.problem.addVariable(variable, domain)
        return self

    def changeVariable(self, variable, domain):
        """Change domain for a variable"""
        self.problem._variables[variable] = Domain(domain)
        return self

    def addConstraint(self, constraint, variables):
        """Add a constraint function applied to a set of variables"""
        self.problem.addConstraint(constraint, variables)
        return self

    def setEventSignupMax(self, event_id, n):
        """Set maximum number of signups for an event"""
        self.addConstraint(lambda count: count <= n, [event_id])

    def setUserSignupMax(self, user_id, n):
        """Set maximum number of signups for a user"""
        self.addConstraint(lambda count: count <= n, [user_id])

    def setEventSignupMin(self, event_id, n):
        """Set minimum number of signups for an event"""
        self.addConstraint(lambda count: count >= n, [event_id])

    def setUserSignupMin(self, user_id, n):
        """Set minimum number of signups for a user"""
        self.addConstraint(lambda count: count >= n, [user_id])

    def getSolutions(self):
        """grabs solutions from constraint problem"""
        return self.problem.getSolutions()

    def getSolutionIter(self):
        """Return iterator of solutions"""
        return self.problem.getSolutionIter()

    def getSolution(self):
        """Return first solution"""
        return next(self.getSolutionIter())

    def __iter__(self):
        return getSolutionIter()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
