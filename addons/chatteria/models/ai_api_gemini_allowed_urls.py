# python

# odoo
from odoo import models, fields


class ApiGeminiAllowedUrls(models.Model):
    _name = 'api.gemini.allowed.urls'

    name = fields.Char(string="url")
    company_id = fields.Many2one('res.company')
    available = fields.Boolean(string="Available", default=True)