from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class CustomerSuccess(models.Model):
    _name = 'customer.success'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Success Record'
    _order = 'sequence_number, id'

    # Core fields
    name = fields.Char(string="Title", required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", tracking=True)

    # Stage + grouping
    stage_id = fields.Many2one(
        'customer.success.stage', string='Stage',
        group_expand='_read_group_stage_ids', tracking=True, ondelete='cascade'
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

    lost_reason_label = fields.Char(
        string="Lost Reason Label",
        compute='_compute_lost_reason_label'
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


    activity_ids = fields.One2many(
        'mail.activity', 'res_id',
        string="Activities",
        domain=[('res_model', '=', 'customer.success')],
    )

    has_call_activity = fields.Boolean(
        string="Has Call Activity", compute="_compute_activity_flags"
    )
    has_email_activity = fields.Boolean(
        string="Has Email Activity", compute="_compute_activity_flags"
    )

    # -------------------------
    # Onchange & Constraints
    # -------------------------

    @api.depends("activity_ids.activity_type_id")
    def _compute_activity_flags(self):
        for rec in self:
            rec.has_call_activity = any(
                a.activity_type_id and a.activity_type_id.default_type == "call"
                for a in rec.activity_ids
            )
            rec.has_email_activity = any(
                a.activity_type_id and a.activity_type_id.default_type == "email"
                for a in rec.activity_ids
            )

    # -------- Onchange handlers CRM and Partner data --------

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """When partner changes, update phone/email (reset first)."""
        self.phone = False
        self.email = False
        if self.partner_id:
            self.phone = self.partner_id.phone or False
            self.email = self.partner_id.email or False

    @api.onchange("related_crm_lead_id")
    def _onchange_related_crm_lead_id(self):
        """When CRM lead changes, update partner, title, phone/email (reset first)."""
        self.partner_id = False
        self.name = False
        self.phone = False
        self.email = False

        if self.related_crm_lead_id:
            lead = self.related_crm_lead_id

            # Fill Partner & Title
            if lead.partner_id:
                self.partner_id = lead.partner_id
            if lead.name:
                self.name = lead.name

            # Fill phone/email (prefer partner, fallback to lead)
            if lead.partner_id:
                self.phone = lead.partner_id.phone or lead.phone or False
                self.email = lead.partner_id.email or lead.email_from or False
            else:
                self.phone = lead.phone or False
                self.email = lead.email_from or False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            lead = None
            if vals.get("related_crm_lead_id"):
                lead = self.env["crm.lead"].browse(vals["related_crm_lead_id"])

                # Only overwrite partner_id if user didn't manually choose it
                if not vals.get("partner_id") and lead.partner_id:
                    vals["partner_id"] = lead.partner_id.id

                # Title always from CRM
                vals["name"] = lead.name or vals.get("name")

            # Fill phone/email from partner if exists
            if vals.get("partner_id"):
                partner = self.env["res.partner"].browse(vals["partner_id"])
                vals["phone"] = partner.phone or vals.get("phone")
                vals["email"] = partner.email or vals.get("email")
            # Fallback: no partner, but lead exists
            elif lead:
                vals["phone"] = lead.phone or vals.get("phone")
                vals["email"] = lead.email_from or vals.get("email")

        return super().create(vals_list)

    def write(self, vals):
        lead = None
        if "related_crm_lead_id" in vals:
            lead = self.env["crm.lead"].browse(vals["related_crm_lead_id"])

            # Only overwrite partner_id if user didn't manually choose it
            if "partner_id" not in vals and lead.partner_id:
                vals["partner_id"] = lead.partner_id.id

            # Title always from CRM
            vals["name"] = lead.name or vals.get("name")

        # Fill phone/email from partner if exists
        if "partner_id" in vals:
            partner = self.env["res.partner"].browse(vals["partner_id"])
            vals["phone"] = partner.phone or vals.get("phone")
            vals["email"] = partner.email or vals.get("email")
        # Fallback: no partner, but lead exists
        elif lead:
            vals["phone"] = lead.phone or vals.get("phone")
            vals["email"] = lead.email_from or vals.get("email")

        return super().write(vals)

    # -------- Onchange handlers CRM and Partner data --------

    def action_open_related_crm_lead(self):
        """Open the related CRM Lead in a form view"""
        self.ensure_one()
        if not self.related_crm_lead_id:
            raise UserError("No related CRM Lead chosen!")
        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM Lead',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': self.related_crm_lead_id.id,
            'target': 'current',
        }

    @api.depends('team_id')
    def _compute_team_user_ids(self):
        """Compute available users based on selected team"""
        for rec in self:
            if rec.team_id:
                users = getattr(rec.team_id, 'user_ids', self.env['res.users'].browse())
                rec.team_user_ids = users
            else:
                rec.team_user_ids = self.env['res.users'].browse()
            rec.team_user_ids = rec.team_id.user_ids if rec.team_id else self.env['res.users'].browse()

    @api.depends('stage_id')
    def _compute_health_percentage(self):
        """Health = 100% if Achieved, 0% if Lost, else relative to pipeline position."""
        all_stages = self.env['customer.success.stage'].search([], order='sequence asc')
        stage_ids = [s.id for s in all_stages]
        for rec in self:
            if rec.stage_id and rec.stage_id.name.lower() == 'won':
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
            rec.active = True
        return True

    def action_set_lost(self):
        """Open wizard instead of directly setting Lost stage."""
        lost = self._get_stage_by_name('Lost')
        if not lost:
            raise UserError("Stage 'Lost' not found. Please create a stage named 'Lost'.")
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Lost',
            'res_model': 'customer.success.lost.reason.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'customer_success.view_customer_success_lost_reason_wizard_form'
                ).id,
            'target': 'new',
            'context': {'default_customer_success_id': self.id},
        }

    @api.depends('stage_id', 'lost_reason_id')
    def _compute_lost_reason_label(self):
        for rec in self:
            if rec.stage_id.name == 'Lost' and rec.lost_reason_id:
                rec.lost_reason_label = f"Lost Reason: {rec.lost_reason_id.name}"
            else:
                rec.lost_reason_label = False

    def toggle_active(self):
        for rec in self:
            rec.active = not bool(rec.active)
        return True

