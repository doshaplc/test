# -*- coding: utf-8 -*-

{
    'name': 'Under Maintenance',
    'category': 'Technical Settings',
    'author': "Mohamed Youssef",
    'website': "http://mohamedhammad.info",
    'summary': 'Put your system under maintenance',
    'description': """
Under Maintenance Module
========================
* This module gives administrator the ability to lock the system for maintenance reasons.
* Only Administrator account has the privilege to login to the system.
* Re-enable login after finishing maintenance.
""",
    'external_dependencies': {
        'python': ['simplejson']
    },
    'depends': [
        'web',
    ],
    'data': [
        "data/ir_config_parameter_data.xml",
        "views/webclient_templates.xml",
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',
    ],
}
