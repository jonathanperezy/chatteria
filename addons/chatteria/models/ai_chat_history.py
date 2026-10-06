# -*- coding: utf-8 -*-
from odoo import models, fields


class AIChatHistory(models.Model):
    _name = 'ai.chat.history'
    _description = 'Stores chat conversations with OpenAI for web chatter and WhatsApp'
    _order = 'create_date asc'

    sender_id = fields.Char(string='Sender ID', required=True, index=True)
    role = fields.Selection([
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('tool', 'Tool')
    ], string='Role', required=True)
    content = fields.Text(string='Content', required=True)
    channel = fields.Selection([
        ('web', 'Web'),
        ('whatsapp', 'WhatsApp')
    ], string='Channel', default='web')
