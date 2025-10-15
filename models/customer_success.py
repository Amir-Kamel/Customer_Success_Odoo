from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class CustomerSuccess(models.Model):
    _name = 'customer.success'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Success Record'
    _order = 'sequence_number, id'

    # Core fields
    name = fields.Char(string="Title", required=True)
    partner_id = fields.Many2one('res.partner', string="Client", tracking=True)

    # Stage + grouping
    stage_id = fields.Many2one(
        'customer.success.stage', string='Stage',
        group_expand='_read_group_stage_ids', tracking=True,ondelete='cascade'
    )
    team_id = fields.Many2one('customer.success.team', string="Team", tracking=True)


    assigned_user_id = fields.Many2one(
        'res.users',
        string="Success Partner",
        domain="[('id', 'in', team_user_ids)]",
        tracking=True
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
    # 1. This special 'related' field magically finds the project from the linked CRM lead.
    #    It will automatically update whenever 'related_crm_lead_id' changes.
    related_project_id = fields.Many2one(
        'project.project',
        related='related_crm_lead_id.project_id',
        string="Related CRM Project",
        readonly=True,
        store=True, # store=True helps with searching and performance
        help="The project associated with the related CRM Lead."
    )

    sequence_number = fields.Integer(string="Sequence")

    # Health bar logic
    health_percentage = fields.Float(
        string="Health %",
        digits=(3, 1),
        compute='_compute_health_percentage',
        store=False
    )

    # NEW: lost reason
    lost_reason_id = fields.Many2one(
        'customer.success.lost.reason',
        string="Churned Reason",
        readonly=True,
        copy=False
    )

    lost_reason_label = fields.Char(
        string="Churned Reason Label",
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

    # 1. Field to count related survey responses
    survey_count = fields.Integer(
        'Survey Count',
        compute='_compute_survey_count'
    )

    def _compute_survey_count(self):
        # We search the new field on survey.user_input
        data = self.env['survey.user_input'].read_group(
            [('customer_success_id', 'in', self.ids)],
            ['customer_success_id'],
            ['customer_success_id']
        )
        count_map = {item['customer_success_id'][0]: item['customer_success_id_count'] for item in data}
        for record in self:
            record.survey_count = count_map.get(record.id, 0)

    # 2. Smart Button Action
    def action_view_participations(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('survey.action_survey_user_input')

        # Filter the results by the current Customer Success record
        action['domain'] = [('customer_success_id', '=', self.id)]
        action['context'] = {'default_customer_success_id': self.id}

        return action


    # 2. This is the action method for our new smart button.
    def action_view_project(self):
        """Opens the related project in a form view."""
        self.ensure_one()
        # This is very similar to the crm.lead action, but it uses our new related field.
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'res_model': 'project.project',
            'view_mode': 'form',
            'res_id': self.related_project_id.id,
        }


    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        # Get all stages ordered by sequence
        stages = self.env['customer.success.stage'].search([], order='sequence asc')

        # Pick the first stage that is NOT Won/Lost
        normal_stage = next((s for s in stages if not s.is_won and not s.is_lost), False)

        if normal_stage:
            res['stage_id'] = normal_stage.id
        else:
            raise UserError(
                "Cannot create a new Customer Success record because "
                "there are no normal stages (other than Achieved/Churned). "
                "Please create at least one normal stage first."
            )

        return res

    # -------- Onchange handlers CRM and Partner data --------

    @api.onchange('related_crm_lead_id')
    def _onchange_related_crm_lead_id(self):
        """Reset all relevant fields, then set title, partner, and phone/email intelligently."""
        lead = self.related_crm_lead_id
        if not lead:
            return
        # Always set the name/title
        self.name = lead.name or False
        self.partner_id = lead.partner_id or False
        self.phone = lead.partner_id.phone or lead.phone or False
        self.email = lead.partner_id.email or lead.email_from or False


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Reset phone/email, then set from partner."""
        if not self.partner_id:
            return

        if self.related_crm_lead_id and self.related_crm_lead_id.partner_id:
            if self.partner_id != self.related_crm_lead_id.partner_id:
                # Revert the change
                self.partner_id = self.related_crm_lead_id.partner_id
                return {
                    'warning': {
                        'title': "Partner cannot be changed",
                        'message': "This record is linked to a CRM lead that already has a partner. "
                                   "You cannot assign a different partner. "
                                    "Choose a partner in this related CRM lead instead.",
                    }
                }

        if self.partner_id:
            self.phone = self.partner_id.phone or False
            self.email = self.partner_id.email or False

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
        """Compute health percentage:
           - 100% for Achieved (Won)
           - 0% for Churned (Lost)
           - Relative for normal stages, capped below 100
        """
        all_stages = self.env['customer.success.stage'].search([], order='sequence asc')
        normal_stages = [s for s in all_stages if not s.is_won and not s.is_lost]

        for rec in self:
            if rec.stage_id:
                if rec.stage_id.is_won:
                    rec.health_percentage = 100
                elif rec.stage_id.is_lost:
                    rec.health_percentage = 0
                elif rec.stage_id in normal_stages:
                    # Relative progress: divide by (total normal stages + 1) to avoid 100%
                    stage_index = normal_stages.index(rec.stage_id)
                    rec.health_percentage = round(
                        (stage_index + 1) / (len(normal_stages) + 1) * 100, 1
                    )

                else:
                    rec.health_percentage = 0
            else:
                rec.health_percentage = 0

    @api.depends('stage_id')
    def _compute_flag(self):
        for rec in self:
            if rec.stage_id and rec.stage_id.name.lower() == 'achieved':
                rec.flag_color = 'green'
            elif rec.stage_id and rec.stage_id.name.lower() == 'churned':
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

    def action_show_success_animation(self):
        self.ensure_one()
        # Your custom message
        message = "🎉 Great! You achieved a new success story! 🌈"

        return {
            'effect': {
                'fadeout': 'slow',
                'message': message,
                'img_url': '/web/static/img/smile.svg',  # optional: you can replace with a team/user image
                'type': 'rainbow_man',  # can stay as 'rainbow_man' or 'success_animation'
            }
        }

    def action_set_won(self):
        won = self._get_stage_by_name('Achieved')
        if not won:
            raise UserError("Stage 'Achieved' not found. Please create a stage marked as 'Achieved'.")
        for rec in self:
            rec.stage_id = won
            rec.active = True
        return self.action_show_success_animation()

    def action_set_lost(self):
        """Open wizard instead of directly setting Lost stage."""
        lost = self._get_stage_by_name('Churned')
        if not lost:
            raise UserError("Stage 'Churned' not found. Please create a stage marked as 'Churned'.")
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Churned',
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
            if rec.stage_id.name == 'Churned' and rec.lost_reason_id:
                rec.lost_reason_label = f"Churned Reason: {rec.lost_reason_id.name}"
            else:
                rec.lost_reason_label = False


    def toggle_active(self):
        for rec in self:
            rec.active = not bool(rec.active)
        return True


    def action_ask_feedback(self):

        template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)

        local_context = {

            'active_id': self.id,           # The ID of the current Customer Success record
            'active_model': self._name,     # The model name ('customer.success')
            'default_template_id': template and template.id or False,
            'default_email_layout_xmlid': 'mail.mail_notification_light',
            'default_send_email': True, # Assume we want to send an email
            'show_survey_template_selection': True,
        }

        return {
            'type': 'ir.actions.act_window',
            'name': _("Ask Feedback"), # New wizard title
            'view_mode': 'form',
            'res_model': 'survey.invite',
            'target': 'new',
            'context': local_context,
        }