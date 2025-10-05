from odoo import models, fields, api

class CustomerSuccessPlan(models.Model):
    _name = 'customer.success.plan'
    _description = 'Customer Success Plan'

    name = fields.Char(string='Plan Description', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    status = fields.Selection([
        ('not_start', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='not_start')

    customer_success_id = fields.Many2one(
        'customer.success',
        string='Customer Success',
        ondelete='cascade'
    )
