# -*- coding: utf-8 -*-
{
    'name': "Hotel Management System",
    'version': '15.0',
    'summary': """Hotel Management System""",
    'description': """The Odoo Hotel Management System is a maestro of automation, orchestrating the day-to-day 
    operations of your hotel with seamless precision. From reservations to check-in/out, room management, 
    and invoicing, Odoo takes care of it all, so you can focus on what matters most: your guests.""",
    'category': 'Productivity',
    'author': "Neoteric Hub",
    'company': 'Neoteric Hub',
    'live_test_url': '',
    'price': 0.0,
    'currency': 'USD',
    'website': 'https://www.neoterichub.com',

    'depends': ['base', 'contacts', 'mail', 'website', 'account', 'board', 'portal'],

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/rooms.xml',
        'views/reservation.xml',
        'views/extra.xml',
        'views/partner.xml',
        'views/templates.xml',
        'report/report.xml',
        'report/reservation_template.xml',
        'views/dashboard.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'css': [
        'static/css/custom.css',  # Add your CSS file here
    ],

    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
