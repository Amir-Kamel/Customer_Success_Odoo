from odoo import models, fields

class CustomerSuccessLostReason(models.Model):
    _name = 'customer.success.lost.reason'
    _description = 'Lost Reason'

    name = fields.Char(string="Reason", required=True)
