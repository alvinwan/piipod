from piiipod.utils.csp import *
import pytest


@pytest.fixture
def events():
    return [chr(i) for i in range(3)]

@pytest.fixture
def users():
    return list(map(str, range(10)))


def test_signupModel(users, events):
    """test that CSP accurately reflects signup relationships"""
    csp = SignupCSP(users, events)
    for sol in csp.getSolutionIter():
        counts = {}
        for user in users:
            for event in events:
                if sol['%s__%s' % (user, event)]:
                    counts.setdefault(user, 0)
                    counts.setdefault(event, 0)
                    counts[user] += 1
                    counts[event] += 1
        for k, v in counts.items():
            assert sol[k] == v
        break

def test_userSignupMax(users, events):
    """test that signups per event are enforced"""
    csp = SignupCSP(users, events)
    for user in users:
        csp.setUserSignupMax(user, 1)
    for sol in csp.getSolutionIter():
        for user in users:
            assert sol[user] <= 1
            assert sum(sol['%s__%s' % (user, event)] for event in events) <= 1
        break

def test_eventSignupMax(users, events):
    """test that signups per event are enforced"""
    csp = SignupCSP(users, events)
    csp.setEventSignupMax('b', 2)
    for sol in csp.getSolutionIter():
        assert sol['b'] <= 2
        break
