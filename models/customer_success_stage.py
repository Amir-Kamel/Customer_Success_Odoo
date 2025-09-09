from odoo import models, fields
class CustomerSuccessStage(models.Model):
    _name = 'customer.success.stage'
    _description = 'Customer Success Stage'
    _order = 'sequence, id'

    name = fields.Char(string="Stage Name", required=True)
    sequence = fields.Integer(string="Sequence", default=1)
    fold = fields.Boolean(string="Folded in Kanban", help="If checked, this stage will be folded by default in the Kanban view.")

    team_id = fields.Many2one('crm.team', string='Sales Team')