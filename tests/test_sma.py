from piipod.utils.sma import SMA


def test_raw_sma():
    """test that raw SMA works"""
    men = {
        'Alex': ('Anita', 'Bridget', 'Christine'),
        'Bob': ('Bridget', 'Anita', 'Christine'),
        'Charles': ('Anita', 'Bridget', 'Christine')
    }
    women = {
        'Anita': ('Bob', 'Alex', 'Charles'),
        'Bridget': ('Alex', 'Bob', 'Charles'),
        'Christine': ('Alex', 'Bob', 'Charles')
    }
    sma = SMA(men, women)
    assert sma.solve() == {('Alex', 'Anita'), ('Bob', 'Bridget'), ('Charles', 'Christine')}
