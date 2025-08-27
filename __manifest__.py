{
    'name': 'Customer Success Management',
    'version': '1.0',
    'summary': 'Track customer health and success metrics',
    'description': """
        Comprehensive customer success tracking with health scores,
        renewal management, and team collaboration
    """,
    'category': 'Customer Relationship Management',
    'depends': ['base', 'crm', 'mail'],
    'data': [
        'views/menu_views.xml',
        'views/customer_success_stage_views.xml',
        'views/customer_success_team_views.xml',
        'views/customer_success_views.xml',
    ],
    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
