# python

# odoo
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    api_gemini_token = fields.Char(string="Gemini Token Access")
    allowed_url_ids = fields.One2many('api.gemini.allowed.urls', 'company_id', string="Allowed Urls")
