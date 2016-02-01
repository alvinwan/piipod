from collections import namedtuple

Man = namedtuple('Man', 'name preferences next')
Woman = namedtuple('Woman', 'name preferences suitor')

class SignupSMA(object):
    """Stable Marriage Algorithm implementation"""




class Man(object):
    """abstraction for man"""

    def __init__(self, name, prefs, next_):
        self.name = name
        self.prefs = dict(enumerate(prefs))
        self.next = next_

class Woman(object):
    """abstraction for woman"""

    def __init__(self, name, prefs, suitor):
        self.name = name
        self.prefs = dict(n[::-1] for n in enumerate(prefs))
        self.suitor = suitor

class SMA(object):
    """generic Stable Marriage Algorithm implementation"""

    def __init__(self, men=(), women=()):
        self.men = {k: Man(k, v, 0) for k, v in men.items()}
        self.women = {k: Woman(k, v, None) for k, v in women.items()}

    def solve(self):
        """Solve stable marriage algorithm"""

        # setup men
        sadMen = sorted(list(self.men.keys()))
        for _, man in self.men.items():
            man.next = 0

        # setup women
        women = self.women
        for _, woman in women.items():
            woman.suitor = None

        # run algorithm
        while sadMen:
            suitor = self.men[sadMen.pop(0)]
            woman = women[suitor.prefs[suitor.next]]
            if not woman.suitor or woman.prefs[suitor.name] < woman.prefs[woman.suitor]:
                if woman.suitor:
                    man = self.men[woman.suitor]
                    man.next += 1
                    sadMen.append(man.name)
                woman.suitor = suitor.name
            else:
                suitor.next += 1
                sadMen.append(suitor.name)

        return set((women[woman].suitor, woman) for woman in women)
