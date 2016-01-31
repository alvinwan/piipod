from piiipod.utils.csp import *
import pytest


@pytest.fixture
def events():
    return [chr(97+i) for i in range(3)]

@pytest.fixture
def users():
    return list(map(str, range(10)))


def test_signupModel(users, events):
    """test that CSP accurately reflects signup relationships"""
    csp = SignupCSP(users, events)
    sol = csp.getSolution()
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

def test_userSignupMax(users, events):
    """test that signups per event are enforced"""
    limit = 1
    csp = SignupCSP(users, events)
    for user in users:
        csp.setUserSignupMax(user, limit)
    sol = csp.getSolution()
    for user in users:
        assert sol[user] <= limit
        assert sum(sol['%s__%s' % (user, event)] for event in events) <= limit

def test_eventSignupMax(users, events):
    """test that signups per event are enforced"""
    limit = 5
    csp = SignupCSP(users, events)
    csp.setEventSignupMax('b', limit)
    sol = csp.getSolution()
    assert sol['b'] <= limit
    assert sum(sol['%s__%s' % (user, 'b')] for user in users) <= limit

def test_userSignupMin(users, events):
    """test that signups per event are enforced"""
    limit = 2
    csp = SignupCSP(users, events)
    for user in users:
        csp.setUserSignupMin(user, limit)
    sol = csp.getSolution()
    for user in users:
        assert sol[user] >= limit
        assert sum(sol['%s__%s' % (user, event)] for event in events) >= limit

def test_eventSignupMin(users, events):
    """test that signups per event are enforced"""
    limit = 8
    csp = SignupCSP(users, events)
    csp.setEventSignupMin('b', limit)
    sol = csp.getSolution()
    assert sol['b'] >= limit
    assert sum(sol['%s__%s' % (user, 'b')] for user in users) >= limit
