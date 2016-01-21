

#################
# DEFAULT ROLES #
#################

default_group_roles = {
    'class': [
        {
            'name': 'Owner',
            'permissions': '*'
        },
        {
            'name': 'Professor',
            'permissions': '*'
        },
        {
            'name': 'GSI',
            'permissions': ''
        },
        {
            'name': 'Reader',
            'permissions': ''
        }],
    'nonprofit': [
        {
            'name': 'Owner',
            'permissions': '*'
        },
        {
            'name': 'Chair',
            'permissions': '*'
        },
        {
            'name': 'Board',
            'permissions': ''
        },
        {
            'name': 'Volunteer',
            'permissions': ''
        }]
}

default_event_roles = {
    'class': [
        {
            'name': 'Owner',
            'permissions': '*'
        },
        {
            'name': 'Authorizer',
            'permissions': 'generate_code'
        },
        {
            'name': 'Participant',
            'permissions': ''
        }
    ],
    'nonprofit': [
        {
            'name': 'Owner',
            'permissions': '*'
        },
        {
            'name': 'Chairperson',
            'permissions': 'generate_code'
        },
        {
            'name': 'Volunteer',
            'permissions': ''
        }
    ]
}
