from odoo import models, fields
from odoo.exceptions import ValidationError

class CustomerSuccessTeam(models.Model):
    _name = 'customer.success.team'
    _description = 'Customer Success Team'

    name = fields.Char(string="Team Name", required=True)
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='customer_success_team_users_rel',
        column1='team_id',
        column2='user_id',
        string="Team Members"

    )

    leader_id = fields.Many2one(
        'res.users',
        string="Team Leader",
        # domain = "[('id', 'in', user_ids)]"  # if want to restrict only to members
    )

    # @api.constrains('leader_id', 'user_ids')
    # def _check_leader_in_users(self):
    #     for team in self:
    #         if team.leader_id and team.leader_id not in team.user_ids:
    #             raise ValidationError("The Team Leader must be one of the Team Members.") # if want to restrict only to members