from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError

class CustomerSuccess(models.Model):
    _name = 'customer.success'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Success Record'

    name = fields.Char(string="Title", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    health_score = fields.Selection(
        [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        string="Health Score", default='medium'
    )
    stage_id = fields.Many2one(
        'customer.success.stage',
        string="Stage",
        group_expand='_read_group_stage_ids',
        ondelete='cascade'
    )
    team_id = fields.Many2one('customer.success.team', string="Team")

    assigned_user_id = fields.Many2one(
        'res.users',
        # limit users from hereeeee from module teams direct
        string="Assigned User",
    )
    # open_ticket_count = fields.Integer(
    #     string="Open Tickets",
    #     compute='_compute_open_ticket_count'
    # )
    last_feedback = fields.Text(string="Last Feedback")
    renewal_date = fields.Date(string="Renewal Date")
    related_crm_lead_id = fields.Many2one('crm.lead', string="Related CRM Lead")
    # related_helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string="Helpdesk Ticket")

    sequence_number = fields.Integer(string="Sequence")  # for kanban order


    # @api.depends('related_helpdesk_ticket_id')
    # def _compute_open_ticket_count(self):
    #     for rec in self:
    #         rec.open_ticket_count = 1 if rec.related_helpdesk_ticket_id else 0

    # Health bar logic: compute percentage based on stage position
    health_percentage = fields.Integer(
        string="Health %",
        compute='_compute_health_percentage',  # do NOT store=True
        store=False
    )

    @api.depends('stage_id')
    def _compute_health_percentage(self):
        all_stages = self.env['customer.success.stage'].search([], order='sequence asc')
        stage_ids = all_stages.ids
        for rec in self:
            if rec.stage_id and rec.stage_id.id in stage_ids:
                stage_index = stage_ids.index(rec.stage_id.id)
                rec.health_percentage = int((stage_index + 1) / len(stage_ids) * 100)
            else:
                rec.health_percentage = 0

    # Limit assigned_user_id to users in team
    @api.onchange('team_id')
    def _onchange_team_users(self):
        if self.team_id:
            return {'domain': {'assigned_user_id': [('id', 'in', self.team_id.user_ids.ids)]}}
        else:
            return {'domain': {'assigned_user_id': []}}

    def _read_group_stage_ids(self, stages, domain, order=None):
        return self.env['customer.success.stage'].search([], order='sequence')






