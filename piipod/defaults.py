

GROUP_PERMISSIONS = ['edit_settings', 'create_event']
EVENT_PERMISSIONS = ['authorize']

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
            'permissions': 'edit_settings, create_event, authorize'
        },
        {
            'name': 'Reader',
            'permissions': ''
        },
        {
            'name': 'Lab Assistant',
            'permissions': ''
        },
        {
            'name': 'Member',
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
            'permissions': 'edit_settings, create_event'
        },
        {
            'name': 'Volunteer',
            'permissions': ''
        },
        {
            'name': 'Member',
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
            'permissions': 'authorize'
        },
        {
            'name': 'Volunteer',
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
            'permissions': 'authorize'
        },
        {
            'name': 'Volunteer',
            'permissions': ''
        }
    ]
}

default_event_settings = {
    'max_check_ins': {
        'label': 'Maximum Number of Checkins',
        'description': 'This is typically one. Disable this setting for no limit.',
        'value': 1,
    },
    'choose_role': {
        'label': 'Users Pick Roles',
        'description': 'Specify roles that new signups can select to be. Disable to auto-assign the default role to new signups.',
        'is_active': False,
        'type': 'boolean'
    },
    'enable_signups': {
        'label': 'Enable Signups',
        'description': 'Allow users to signup',
        'type': 'boolean'
    },
    'enable_leave': {
        'label': 'Enable Leave',
        'description': 'Allow users to leave event',
        'type': 'boolean'
    },
    'categories': {
        'label': 'Available categories',
        'description': 'Comma-separated list of all possible categories (on top of <code>Waitlisted, Accepted</code>)',
        'value': 'Pending',
        'toggable': False
    },
    'default_category': {
        'label': 'Default Category',
        'description': 'New signups are automatically placed in this category.',
        'value': 'Waitlisted',
        'is_active': True,
        'toggable': False,
    },
    'role': {
        'label': 'Default Role',
        'description': 'Specify a default role for this event',
        'value': 'Volunteer'
    }
}

default_group_settings = {
    'whitelist': {
        'label': 'Whitelist',
        'description': 'Whitelist staff members as user1@berkeley.edu(Position), user2@berkeley.edu(Position2),...',
        'value': ''
    },
    'choose_role': {
        'label': 'Users Pick Roles',
        'description': 'Specify roles that new signups can select to be. Disable to auto-assign the default role to new signups.',
        'is_active': False,
    },
    'role': {
        'label': 'Default Role',
        'description': 'Pick the default role for this group upon signup.',
        'value': 'Member',
        'type': 'select',
        'value': ''
    },
    'googlecalendar': {
        'label': 'Google Calendars',
        'description': 'Add your Google Calendar IDs below. Each ID will generally have the form of <code>[token]@group.calendar.google.com</code>.',
        'value': '',
    }
}

# dgs = default_group_settings
# default_group_settings = {
#     'default_%s' % k:v.copy() for k, v in default_event_settings.items()}
# default_group_settings.update(dgs)

default_user_settings = {
    'authorize_code': {
        'value': '$i1lY'
    }
}
