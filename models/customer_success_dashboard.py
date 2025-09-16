# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class CustomerSuccessDashboardContacts(models.Model):
    _name = "customer.success.dashboard.contacts"
    _description = "Customer Success Dashboard - Partner Cards"

    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    name = fields.Char(string="Name", compute='_compute_name', store=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    average_health = fields.Float(string="Average Journey", digits=(3, 1), default=0.0)
    record_count = fields.Integer(string="Journey Stories", default=0)
    success_ids = fields.Many2many('customer.success', string="Success Journeys")
    partner_avatar_128 = fields.Image(
        string="Partner Avatar",
        related='partner_id.avatar_128',
        readonly=True,
    )

    dashboard_id = fields.Many2one(
        comodel_name="customer.success.dashboard.page",
        string="Dashboard",
        ondelete='cascade',
    )


    def action_open_success_journeys(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Customer Success Journeys",
            "res_model": "customer.success",
            "view_mode": "kanban,form",
            "domain": [("id", "in", self.success_ids.ids)],
        }

    @api.depends('partner_id')
    def _compute_name(self):
        for rec in self:
            if rec.partner_id:
                rec.name = rec.partner_id.name or rec.partner_id.email or '—'
            else:
                rec.name = '—'

    @api.model
    def recompute_all(self):
        # Get the parent dashboard page record
        dashboard_page = self.env['customer.success.dashboard.page']._get_or_create_record()
        CustomerSuccess = self.env['customer.success'].sudo()
        Partner = self.env['res.partner'].sudo()
        dashboard_env = self.sudo()

        mapping = {}
        for cs in CustomerSuccess.search([]):
            pid = cs.partner_id.id if cs.partner_id else False
            mapping.setdefault(pid, [])
            mapping[pid].append(int(cs.health_percentage or 0))

        for pid, health_list in mapping.items():
            if not pid:
                continue
            partner = Partner.browse(pid)
            avg = sum(health_list) / len(health_list) if health_list else 0
            rec_count = len(health_list)
            success_ids = CustomerSuccess.search([('partner_id', '=', pid)]).ids

            vals = {
                'phone': partner.phone or '',
                'email': partner.email or '',
                'average_health': avg,
                'record_count': rec_count,
                'success_ids': [(6, 0, success_ids)],
                'dashboard_id': dashboard_page.id,
            }
            db_rec = dashboard_env.search([('partner_id', '=', pid)], limit=1)
            if db_rec:
                db_rec.write(vals)
            else:
                vals['partner_id'] = pid
                dashboard_env.create(vals)

        # remove old records
        all_ids = [p for p in mapping.keys() if p]
        old_recs = dashboard_env.search([('partner_id', 'not in', all_ids)])
        if old_recs:
            old_recs.unlink()
        return True


class CustomerSuccessDashboardAnalytics(models.Model):
    _name = "customer.success.dashboard.analytics"
    _description = "Customer Success Dashboard - Analytics"

    average_health = fields.Float(string="Average Health", digits=(3, 1), default=0.0)

    # JSON payloads consumed by the kanban template
    top_customers_data = fields.Text(string="Top Customers Data")
    bottom_customers_data = fields.Text(string="Bottom Customers Data")

    dashboard_id = fields.Many2one(
        comodel_name="customer.success.dashboard.page",
        string="Dashboard",
        ondelete='cascade',
    )


    @api.model
    def recompute_all(self):
        # Get the parent dashboard page record
        dashboard_page = self.env['customer.success.dashboard.page']._get_or_create_record()
        """Compute global average + top/bottom 5 per partner.
        """
        CustomerSuccess = self.env['customer.success'].sudo()
        Partner = self.env['res.partner'].sudo()
        dashboard_env = self.sudo()

        # build mapping partner_id -> list of health_percentages (floats)
        mapping = {}
        for cs in CustomerSuccess.search([]):
            pid = cs.partner_id.id if cs.partner_id else False
            mapping.setdefault(pid, [])
            # ensure numeric float
            try:
                mapping[pid].append(float(cs.health_percentage or 0.0))
            except Exception:
                mapping[pid].append(0.0)

        # global average
        all_health = [h for lst in mapping.values() for h in lst]
        global_avg = sum(all_health) / len(all_health) if all_health else 0.0

        # partner averages
        partner_avgs = [
            (pid, (sum(vals) / len(vals)))
            for pid, vals in mapping.items() if pid
        ]
        sorted_avgs = sorted(partner_avgs, key=lambda x: x[1], reverse=True)
        top5 = sorted_avgs[:5]
        bottom5 = sorted_avgs[-5:][::-1]


        # JSON payloads (list of dicts)
        top_json = []
        bottom_json = []
        for pid, avg in top5:
            partner = Partner.browse(pid)
            top_json.append({'name': partner.name or '—', 'health': round(avg, 1)})
        for pid, avg in bottom5:
            partner = Partner.browse(pid)
            bottom_json.append({'name': partner.name or '—', 'health': round(avg, 1)})

        vals = {
            'average_health': global_avg,
            'top_customers_data': json.dumps(top_json),
            'bottom_customers_data': json.dumps(bottom_json),
            'dashboard_id': dashboard_page.id,
        }

        rec = dashboard_env.search([], limit=1)
        if rec:
            rec.write(vals)
        else:
            dashboard_env.create(vals)
        return True


class CustomerSuccess(models.Model):
    _inherit = 'customer.success'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self.env['customer.success.dashboard.contacts'].recompute_all()
        self.env['customer.success.dashboard.analytics'].recompute_all()
        return res

    def write(self, vals):
        res = super().write(vals)
        self.env['customer.success.dashboard.contacts'].recompute_all()
        self.env['customer.success.dashboard.analytics'].recompute_all()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['customer.success.dashboard.contacts'].recompute_all()
        self.env['customer.success.dashboard.analytics'].recompute_all()
        return res


# In your Python file (e.g., models/customer_success_dashboard_page.py)

class CustomerSuccessDashboardPage(models.Model):
    _name = "customer.success.dashboard.page"
    _description = "Unified Customer Success Dashboard Page"

    name = fields.Char(default="Customer Success Dashboard", readonly=True)

    # Links to the other models
    analytics_ids = fields.One2many(
        "customer.success.dashboard.analytics",
        "dashboard_id",
        string="Analytics Data"
    )
    contact_ids = fields.One2many(
        "customer.success.dashboard.contacts",
        "dashboard_id",
        string="Contact Cards"
    )

    # Helper method to always get the single dashboard record DEFINED IN XML
    @api.model
    def _get_or_create_record(self):
        # This now reliably finds the record created in the XML file.
        # Replace 'customer_success' with your actual module name if different.
        return self.env.ref('customer_success.main_dashboard_page_record')

    # Optional: A button or method to manually refresh all data
    def action_recompute_dashboards(self):
        self.ensure_one() # Good practice to ensure it runs on a single record
        self.env['customer.success.dashboard.analytics'].recompute_all()
        self.env['customer.success.dashboard.contacts'].recompute_all()