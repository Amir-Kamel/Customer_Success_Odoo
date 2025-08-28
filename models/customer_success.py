from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

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
        string="Success Partner",
        domain="[('id', 'in', team_user_ids)]",
    )

    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    # helper field (not visible in form, computed automatically)
    team_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_team_users',
        store=False
    )

    last_feedback = fields.Text(string="Feedback")
    renewal_date = fields.Date(string="Renewal Date")
    related_crm_lead_id = fields.Many2one('crm.lead', string="Related CRM Lead")


    sequence_number = fields.Integer(string="Sequence")  # for kanban order

    # Health bar logic: compute percentage based on stage position
    health_percentage = fields.Integer(
        string="Health %",
        compute='_compute_health_percentage',
        store=False
    )

    tag_ids = fields.Many2many(
        comodel_name="csm.tag",
        string="Tags"
    )


    @api.onchange('related_crm_lead_id')
    def _onchange_related_crm_lead_id(self):
        if self.related_crm_lead_id:
            # Fill partner
            self.partner_id = self.related_crm_lead_id.partner_id
            # Fill phone and email from CRM lead
            self.phone = self.related_crm_lead_id.phone or self.related_crm_lead_id.partner_id.phone
            self.email = self.related_crm_lead_id.email_from or self.related_crm_lead_id.partner_id.email
            # Fill title (name)
            self.name = self.related_crm_lead_id.name

    def action_open_related_crm_lead(self):
        """Open the related CRM Lead in a form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM Lead',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': self.related_crm_lead_id.id,
            'target': 'current',
        }

    @api.depends('team_id')
    def _compute_team_users(self):
        """Compute available users based on selected team"""
        for rec in self:
            rec.team_user_ids = rec.team_id.user_ids if rec.team_id else False

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


    @api.constrains('team_id', 'assigned_user_id')
    def _check_assigned_user_in_team(self):
        for rec in self:
            if rec.team_id and rec.assigned_user_id and rec.assigned_user_id not in rec.team_id.user_ids:
                raise ValidationError("Assigned user must be a member of the selected team.")


    def _read_group_stage_ids(self, stages, domain, order=None):
        return self.env['customer.success.stage'].search([], order='sequence')







