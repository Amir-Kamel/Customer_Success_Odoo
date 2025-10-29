{
    'name': 'Customer Success Management',
    'version': '18.0',
    'summary': 'Track customer health and success metrics',
    'description': """
        Comprehensive customer success tracking with health scores,
        renewal management, and team collaboration
    """,
    'category': 'Customer Relationship Management',
    'depends': ['base','web','crm', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'data/data.xml',
        'views/customer_success_lost_reason_view.xml',
        'views/customer_success_stage_views.xml',
        'views/customer_success_team_views.xml',
        'views/customer_success_views.xml',
        'views/crm_lead_views.xml',
        'views/contact_view.xml',
        'views/customer_success_tags_views.xml',
        'views/customer_success_dashboard_page_views.xml',
        'views/customer_success_dashboard_analytics_views.xml',
        'views/customer_success_dashboard_contacts_views.xml',
        'views/menu_views.xml',
        'views/survey_invite_inherit_views.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'customer_success/static/src/css/customer_success_styles.css',
        ],
    },
    'installable': True,
    'application': True,
     'sequence': 1,
    'auto_install': False,
    'license': 'LGPL-3',
}
