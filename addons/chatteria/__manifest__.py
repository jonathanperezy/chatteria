{
    'sequence': 0,
    'name': 'chatteria',
    'summary': 'Chatter with IA Integration',
    'description': "",
    'version': '0.0.2',
    'application': True,
    'author': 'Jonathan Perez',
    'depends': [
        'base', 'sale', 'sale_management', 'sales_team',
    ],
    'pre_init_hook': 'pre_init_hooks',
    'data': [
        'security/security.xml',
        'security/admin/ir.model.access.csv',
        'security/gemini/ir.model.access.csv',
        
        'views/res_company_views.xml',
    ]
}