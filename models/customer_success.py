from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class CustomerSuccess(models.Model):
    _name = 'customer.success'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Success Record'
    _order = 'sequence_number, id'

    # show_achieved_btn = fields.Boolean(string='Show Achieved Button',
    #                                    compute='_compute_stage_buttons',
    #                                    store=False)
    # show_lost_btn = fields.Boolean(string='Show Lost Button',
    #                                compute='_compute_stage_buttons',
    #                                store=False)

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
        group_expand='_read_group_stage_ids', tracking=True,
    )

    probability = fields.Integer(string='Probability', default=0)
    team_id = fields.Many2one('crm.team', string="Team")
    assigned_user_id = fields.Many2one(
        'res.users', string="Success Partner",
        domain="[('id','in', team_user_ids and team_user_ids.ids or [])]"
    )
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    last_feedback = fields.Text(string="Feedback")
    renewal_date = fields.Date(string="Renewal Date")
    related_crm_lead_id = fields.Many2one('crm.lead', string="Related CRM Lead")
    sequence_number = fields.Integer(string="Sequence")
    health_percentage = fields.Integer(
        string="Health %",
        compute='_compute_health_percentage',
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
        [('new', 'New'), ('proposition', 'Proposition'), ('opportunity', 'Opportunity'), ('lead', 'Lead')],
        string='Type', default='new', required=True
    )

    # helper many2many of team users (computed)
    team_user_ids = fields.Many2many(
        'res.users',
        string='Team Users',
        compute='_compute_team_user_ids',
        store=False,
    )


    @api.depends('team_id')
    def _compute_team_user_ids(self):
        for rec in self:
            if rec.team_id:

                users = getattr(rec.team_id, 'user_ids', self.env['res.users'].browse())
                rec.team_user_ids = users
            else:
                rec.team_user_ids = self.env['res.users'].browse()

    @api.depends('stage_id')
    def _compute_health_percentage(self):
        all_stages = self.env['customer.success.stage'].search([], order='sequence asc')
        stage_ids = [s.id for s in all_stages]
        for rec in self:
            if rec.stage_id and rec.stage_id.id in stage_ids and len(stage_ids) > 0:
                idx = stage_ids.index(rec.stage_id.id)
                rec.health_percentage = int((idx + 1) / len(stage_ids) * 100)
            else:
                rec.health_percentage = 0

    @api.constrains('team_id', 'assigned_user_id')
    def _check_assigned_user_in_team(self):
        for rec in self:
            if rec.team_id and rec.assigned_user_id and rec.assigned_user_id not in rec.team_id.user_ids:
                raise ValidationError("Assigned user must be a member of the selected team.")


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

        lost = self._get_stage_by_name('Lost')
        if not lost:
            raise UserError("Stage 'Lost' not found. Please create a stage named 'Lost'.")
        for rec in self:
            rec.stage_id = lost
            rec.probability = 0
        return True

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

    # Convert to CRM opportunity (create crm.lead)
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



    # def action_open_related_crm_lead(self):
    #
    #     Lead = self.env['crm.lead']
    #     leads = self.mapped('related_crm_lead_id').filtered(lambda r: bool(r))
    #     if not leads:
    #         # No related leads — helpful UserError so the user knows why button is hidden normally.
    #         raise UserError("No related CRM Opportunity/Lead is linked to this record.")
    #     # If only one lead, open it in form
    #     if len(leads) == 1:
    #         lead = leads[0]
    #         view = self.env.ref('crm.crm_case_form_view_oppor', False)
    #         return {
    #             'name': 'Opportunity',
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'crm.lead',
    #             'res_id': lead.id,
    #             'view_mode': 'form',
    #             'view_id': view and view.id or False,
    #             'target': 'current',
    #         }
    #     # For many leads (unlikely with a Many2one), show list
    #     return {
    #         'name': 'Opportunities',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'crm.lead',
    #         'domain': [('id', 'in', leads.ids)],
    #         'view_mode': 'tree,form',
    #         'target': 'current',
    #     }




    def action_open_related_crm_lead(self):
        self.ensure_one()
        leads = self.mapped('related_crm_lead_id').filtered(lambda r: bool(r))
        if not leads:
            raise UserError(_("No related CRM Opportunity/Lead is linked to this record."))

        readonly_ctx = {
            'form_view_initial_mode': 'view',
            'create': False,
            'edit': False,
            'delete': False,
        }

        # single
        if len(leads) == 1:
            lead = leads[0]
            form_view = self.env.ref('crm.crm_case_form_view_oppor', raise_if_not_found=False)
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Opportunity'),
                'res_model': 'crm.lead',
                'res_id': lead.id,
                'view_mode': 'form',
                'target': 'current',
                'context': readonly_ctx,
            }
            if form_view:
                action['views'] = [(form_view.id, 'form')]
                action['view_id'] = form_view.id
            return action

        # multiple
        tree_view = self.env.ref('crm.crm_case_tree_view_oppor', raise_if_not_found=False)
        form_view = self.env.ref('crm.crm_case_form_view_oppor', raise_if_not_found=False)
        views = []
        if tree_view:
            views.append((tree_view.id, 'tree'))
        if form_view:
            views.append((form_view.id, 'form'))

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Opportunities'),
            'res_model': 'crm.lead',
            'domain': [('id', 'in', leads.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
            'context': readonly_ctx,
        }
        if views:
            action['views'] = views
        return action




# ---- top-level CRM lead extension (must be outside CustomerSuccess class) ----
class CrmLeadInherit(models.Model):
    _inherit = "crm.lead"

    def write(self, vals):
        res = super().write(vals)
        # if stage changed, check for Won
        if 'stage_id' in vals:
            won_stage = self.env['crm.stage'].search([('name', '=', 'Won')], limit=1)
            cs_model = self.env['customer.success']
            first_stage = self.env['customer.success.stage'].search([], order='sequence asc', limit=1)
            for lead in self:
                if won_stage and lead.stage_id and lead.stage_id.id == won_stage.id:
                    existing = cs_model.search([('related_crm_lead_id', '=', lead.id)], limit=1)
                    if existing:
                        continue
                    vals_cs = {
                        'name': lead.name or _('Opportunity: %s') % lead.id,
                        'partner_id': lead.partner_id.id or False,
                        'phone': getattr(lead, 'phone', False) or getattr(lead, 'contact_phone', False) or False,
                        'email': lead.email_from or False,
                        'stage_id': first_stage.id if first_stage else False,
                        'related_crm_lead_id': lead.id,
                        'last_feedback': lead.description or False,
                    }

        return res






