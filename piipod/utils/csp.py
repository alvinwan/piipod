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

    Model:
    - All event variables are mapped to a per-event signup count.
    - All user variables are mapped to a per-user signup count.
    - All signups are modeled using a variable with [0, 1], where 0 is signed up
        and 1 is not.
    """

    def __init__(self, user_ids, event_ids):
        """Accepts iterables of user ids and event ids"""
        self.problem = Problem()
        check = lambda *args: args[-1] == sum(args[:-1])

        for uid in user_ids:

            # add user to problem
            self.addVariable(uid, list(range(len(event_ids)+1)))

            # add signups to problem
            signups = ['%s__%s' % (str(uid), str(eid)) for eid in event_ids]
            for signup in signups:
                self.addVariable(signup, [0, 1])

            # ensure user count is actually equal to sum of all signups
            self.addConstraint(check, signups + [uid])

        for eid in event_ids:

            # add event to problem
            self.addVariable(eid, list(range(len(user_ids)+1)))

            # ensure event count is actually equal to sum of all signups
            signups = ['%s__%s' % (str(uid), str(eid)) for uid in user_ids]
            self.addConstraint(check, signups + [eid])

    #################
    # CSP UTILITIES #
    #################

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

    ####################
    # SIGNUP CSP MODEL #
    ####################

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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
