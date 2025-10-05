
from odoo import models, fields

class CustomerSuccessObjective(models.Model):
    _name = 'customer.success.objective'
    _description = 'Customer Success Objective'

    name = fields.Char(string='Objective', required=True)
    is_done = fields.Boolean(string='Done')
    customer_success_id = fields.Many2one('customer.success', string='Customer Success', ondelete='cascade')
