from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class CustomerSuccess(models.Model):
    _name = 'customer.success'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Success Record'
    _order = 'sequence_number, id'

    # Core fields
    name = fields.Char(string="Title", required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", tracking=True)
    health_score = fields.Selection(
        [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        string="Health Score", default='medium'
    )

    # Stage + grouping
    stage_id = fields.Many2one(
        'customer.success.stage', string='Stage',
        group_expand='_read_group_stage_ids', tracking=True, ondelete='cascade'
    )
    team_id = fields.Many2one('customer.success.team', string="Team")

    probability = fields.Integer(string='Probability', default=0)

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
        compute='_compute_team_user_ids',
        store=False
    )

    last_feedback = fields.Html(string="Feedback")
    renewal_date = fields.Date(string="Renewal Date")
    related_crm_lead_id = fields.Many2one('crm.lead', string="Related CRM Lead")
    sequence_number = fields.Integer(string="Sequence")

    # Health bar logic
    health_percentage = fields.Integer(
        string="Health %",
        compute='_compute_health_percentage',
        store=False
    )

    # NEW: lost reason
    lost_reason_id = fields.Many2one(
        'customer.success.lost.reason',
        string="Lost Reason",
        readonly=True,
        copy=False
    )

    # NEW: flag indicator (green/red/none)
    flag_color = fields.Selection(
        [('green', 'Green'), ('red', 'Red'), ('none', 'None')],
        string="Flag",
        compute="_compute_flag",
        store=False
    )

    tag_ids = fields.Many2many('csm.tag', string="Tags")
    priority = fields.Selection(
        [
            ("0", "Normal"),
            ("1", "Low"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        string="Priority",
        default="0",
        index=True,
    )

    # Visibility / workflow helpers
    active = fields.Boolean(string='Active', default=True)
    type = fields.Selection(
        [('new', 'New'), ('proposition', 'Proposition'),
         ('opportunity', 'Opportunity'), ('lead', 'Lead')],
        string='Type', default='new', required=True
    )

    # -------------------------
    # Onchange & Constraints
    # -------------------------
    @api.onchange('related_crm_lead_id')
    def _onchange_related_crm_lead_id(self):
        if self.related_crm_lead_id:
            self.partner_id = self.related_crm_lead_id.partner_id
            self.phone = self.related_crm_lead_id.phone or self.related_crm_lead_id.partner_id.phone
            self.email = self.related_crm_lead_id.email_from or self.related_crm_lead_id.partner_id.email
            self.name = self.related_crm_lead_id.name

    @api.depends('team_id')
    def _compute_team_user_ids(self):
        for rec in self:
            rec.team_user_ids = rec.team_id.user_ids if rec.team_id else False

    @api.depends('stage_id')
    def _compute_health_percentage(self):
        """Health = 100% if Achieved, 0% if Lost, else relative to pipeline position."""
        all_stages = self.env['customer.success.stage'].search([], order='sequence asc')
        stage_ids = [s.id for s in all_stages]
        for rec in self:
            if rec.stage_id and rec.stage_id.name.lower() == 'achieved':
                rec.health_percentage = 100
            elif rec.stage_id and rec.stage_id.name.lower() == 'lost':
                rec.health_percentage = 0
            elif rec.stage_id and rec.stage_id.id in stage_ids and len(stage_ids) > 0:
                stage_index = stage_ids.index(rec.stage_id.id)
                rec.health_percentage = int((stage_index + 1) / len(stage_ids) * 100)
            else:
                rec.health_percentage = 0

    @api.depends('stage_id')
    def _compute_flag(self):
        for rec in self:
            if rec.stage_id and rec.stage_id.name.lower() == 'achieved':
                rec.flag_color = 'green'
            elif rec.stage_id and rec.stage_id.name.lower() == 'lost':
                rec.flag_color = 'red'
            else:
                rec.flag_color = 'none'

    @api.constrains('team_id', 'assigned_user_id')
    def _check_assigned_user_in_team(self):
        for rec in self:
            if rec.team_id and rec.assigned_user_id and rec.assigned_user_id not in rec.team_id.user_ids:
                raise ValidationError("Assigned user must be a member of the selected team.")

    # -------------------------
    # Group Expansion
    # -------------------------
    def _read_group_stage_ids(self, stages, domain, order=None):
        return self.env['customer.success.stage'].search([], order='sequence')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None, *args, **kwargs):
        order = order or 'sequence asc'
        Stage = self.env['customer.success.stage']
        stage_records = Stage.sudo().search([], order=order)
        return Stage.browse(stage_records.ids)

    # -------------------------
    # Workflow action methods
    # -------------------------
    def _get_stage_by_name(self, name):
        return self.env['customer.success.stage'].search([('name', '=', name)], limit=1)

    def action_set_won(self):
        won = self._get_stage_by_name('Won')
        if not won:
            raise UserError("Stage 'Won' not found. Please create a stage named 'Won'.")
        for rec in self:
            rec.stage_id = won
            rec.probability = 100
            rec.active = True
        return True

    def action_set_lost(self):
        """Open wizard instead of directly setting Lost stage."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Lost',
            'res_model': 'customer.success.lost.reason.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'Customer_Success_Odoo.view_customer_success_lost_reason_wizard_form'
            ).id,
            'target': 'new',
            'context': {'default_customer_success_id': self.id},
        }

    def action_set_proposition(self):
        prop = self._get_stage_by_name('Proposition')
        if not prop:
            raise UserError("Stage 'Proposition' not found. Please create a stage named 'Proposition'.")
        for rec in self:
            rec.stage_id = prop
            rec.probability = 50
        return True

    def action_set_new(self):
        new = self._get_stage_by_name('New')
        if not new:
            raise UserError("Stage 'New' not found. Please create a stage named 'New'.")
        for rec in self:
            rec.stage_id = new
            rec.probability = 10
        return True

    def toggle_active(self):
        for rec in self:
            rec.active = not bool(rec.active)
        return True

    # -------------------------
    # CRM conversion
    # -------------------------
    def action_convert_to_opportunity(self):
        Lead = self.env['crm.lead']
        created = self.env['crm.lead']
        for rec in self:
            if rec.related_crm_lead_id:
                created |= rec.related_crm_lead_id
                continue
            vals = {
                'name': rec.name or 'Opportunity from Customer Success',
                'partner_id': rec.partner_id.id or False,
                'phone': rec.phone or False,
                'email_from': rec.email or False,
            }
            lead = Lead.create(vals)
            rec.related_crm_lead_id = lead
            rec.type = 'opportunity'
            created |= lead

        if len(created) == 1:
            lead = created
            view = self.env.ref('crm.crm_case_form_view_oppor', False)
            return {
                'name': 'Opportunity',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'res_id': lead.id,
                'view_mode': 'form',
                'view_id': view and view.id or False,
                'target': 'current',
            }
        elif created:
            return {
                'name': 'Opportunities',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'domain': [('id', 'in', created.ids)],
                'view_mode': 'tree,form',
                'target': 'current',
            }
        return True

    def action_open_related_crm_lead(self):
        leads = self.mapped('related_crm_lead_id').filtered(lambda r: bool(r))
        if not leads:
            raise UserError("No related CRM Opportunity/Lead is linked to this record.")
        if len(leads) == 1:
            lead = leads[0]
            view = self.env.ref('crm.crm_case_form_view_oppor', False)
            return {
                'name': 'Opportunity',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'res_id': lead.id,
                'view_mode': 'form',
                'view_id': view and view.id or False,
                'target': 'current',
            }
        return {
            'name': 'Opportunities',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'domain': [('id', 'in', leads.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }
