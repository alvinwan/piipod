

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

default_event_settings = {
    'max_check_ins': {
        'value': 1
    }
}

default_group_settings = {

}

dgs = default_group_settings
default_group_settings = {
    'default_%s' % k:v.copy() for k, v in default_event_settings.items()}
default_group_settings.update(dgs)

default_user_settings = {
    'authorize_code': {
        'value': '$i1lY'
    }
}
