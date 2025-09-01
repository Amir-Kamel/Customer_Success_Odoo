{
    'name': 'Customer Success Management',
    'version': '18.0',
    'summary': 'Track customer health and success metrics',
    'description': """
        Comprehensive customer success tracking with health scores,
        renewal management, and team collaboration
    """,
    'category': 'Customer Relationship Management',
    'depends': ['base', 'crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_success_stage_views.xml',
        'views/customer_success_team_views.xml',
        'views/customer_success_views.xml',
        'views/customer_success_tags_views.xml',
        'views/menu_views.xml',

    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'customer_success/static/src/css/customer_success_styles.css',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
