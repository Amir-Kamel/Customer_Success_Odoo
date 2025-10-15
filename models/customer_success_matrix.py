from odoo import models, fields, api

class CustomerSuccessMatrix(models.Model):
    _name = 'customer.success.matrix'
    _description = 'Key Success Matrix'

    name = fields.Char(string='Description', required=True)
    is_done = fields.Boolean(string='Done')

    percentage = fields.Float(string='Percentage', compute='_compute_percentage', store=True)

    customer_success_id = fields.Many2one(
        'customer.success',
        string='Customer Success',
        ondelete='cascade'
    )

    @api.depends('customer_success_id.matrix_ids')
    def _compute_percentage(self):
        for record in self:
            if record.customer_success_id and record.customer_success_id.matrix_ids:
                total_lines = len(record.customer_success_id.matrix_ids)
                record.percentage = 100.0 / total_lines if total_lines > 0 else 0.0
            else:
                record.percentage = 0.0
