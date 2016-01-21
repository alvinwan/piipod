

#################
# DEFAULT ROLES #
#################

default_group_roles = {
    'class': [
        {
            'name': 'Professor',
            'permissions': '*'
        },
        {
            'shortname': 'GSI',
            'name': 'Graduate Student Instructor',
            'permissions': ''
        },
        {
            'name': 'Reader',
            'permissions': ''
        }],
    'nonprofit': [
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
            'name': 'Chairperson',
            'permissions': 'generate_code'
        },
        {
            'name': 'Volunteer',
            'permissions': ''
        }
}
