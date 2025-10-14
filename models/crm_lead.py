from odoo import models,fields,api
from datetime import timedelta
from odoo import tools


class CrmLead(models.Model):
    _inherit = "crm.lead"

    create_cs = fields.Selection(
        selection=[('yes', 'Yes'), ('no', 'No')],
        string='Customer Success Needed?',
        default=False,  # Starts blank/unset
    )
    is_won = fields.Boolean(
        string='Is Won Stage?',
        compute='_compute_is_won',
        store=False,
    )
    related_cs_id = fields.Many2one(
        'customer.success',
        string='Related Customer Success',
        compute='_compute_related_cs',
        store=False,
    )
    cs_count = fields.Integer(
        string='Customer Success Count',
        compute='_compute_cs_count',
        store=False,
    )
    show_cs_button = fields.Boolean(
        string='Show Customer Success Button',
        compute='_compute_show_cs_button',
        store=False,
    )

    @api.depends('stage_id')
    def _compute_is_won(self):
        for rec in self:
            rec.is_won = rec._is_won_stage(rec.stage_id)

    def _compute_related_cs(self):
        for rec in self:
            cs = self.env['customer.success'].search([('related_crm_lead_id', '=', rec.id)], limit=1)
            rec.related_cs_id = cs.id if cs else False

    @api.depends('related_cs_id')
    def _compute_cs_count(self):
        for rec in self:
            rec.cs_count = 1 if rec.related_cs_id else 0

    @api.depends('create_cs')
    def _compute_show_cs_button(self):
        for rec in self:
            rec.show_cs_button = rec.create_cs == 'yes'

    def _get_customer_success_stage(self):
        stage_record = self.env.ref('Customer_Success.customer_success_stage_welcome', raise_if_not_found=False)
        if not stage_record:
            stage_model = self.env['customer.success.stage']
            stage_record = stage_model.search([('name', '=', 'On Boarding')], limit=1)
            if not stage_record:
                stage_record = stage_model.create({'name': 'On Boarding'})
        return stage_record

    def _get_customer_success_initial_stage(self):
        """Return the first normal customer.success.stage (not is_won and not is_lost).
        Fallback to Achieved stage if none found."""
        stage = self.env['customer.success.stage'].search(
            [('is_won', '=', False), ('is_lost', '=', False)],
            order='sequence asc',
            limit=1
        )
        if stage:
            return stage
        return self._get_customer_success_stage()

    def _is_won_stage(self, stage):
        if not stage:
            return False

        if hasattr(stage, 'probability') and stage.probability is not None:
            try:
                if float(stage.probability) >= 100.0:
                    return True
            except Exception:
                pass

        name = (stage.name or '').strip().lower()
        keywords = ['won', 'achieved', 'win']
        for k in keywords:
            if k in name:
                return True

        return False

    def _lead_phone_email(self, lead):
        """Helper to choose phone/email from partner first, then lead fields."""
        phone = False
        email = False
        if lead:
            if lead.partner_id:
                phone = lead.partner_id.phone or False
                email = lead.partner_id.email or False
            # if still empty take from lead
            if not phone:
                phone = lead.phone or False
            if not email:
                email = lead.email_from or False
        return phone, email


    def action_set_won(self):
        res = super().action_set_won()

        CustomerSuccess = self.env['customer.success']
        initial_stage = self._get_customer_success_initial_stage()
        stage_id = initial_stage.id if initial_stage else False

        to_create = []
        for lead in self:
            exists = CustomerSuccess.search([('related_crm_lead_id', '=', lead.id)], limit=1)
            if exists:
                continue

            phone, email = self._lead_phone_email(lead)

            vals = {
                'name': lead.name or ('Customer Success for: %s' % (lead.id,)),
                'partner_id': lead.partner_id.id or False,
                'related_crm_lead_id': lead.id,
                'stage_id': stage_id,
                'phone': phone,
                'email': email,
            }
            to_create.append(vals)

        if to_create:
            CustomerSuccess.create(to_create)

        return res



    def action_open_cs(self):

        self.ensure_one()
        CustomerSuccess = self.env['customer.success']

        # find existing CS
        cs = CustomerSuccess.search([('related_crm_lead_id', '=', self.id)], limit=1)
        if not cs:
            # create minimal Customer Success record (reuse helper logic)
            initial_stage = self._get_customer_success_initial_stage()
            stage_id = initial_stage.id if initial_stage else False
            phone, email = self._lead_phone_email(self)
            vals = {
                'name': self.name or ('Customer Success for: %s' % (self.id,)),
                'partner_id': self.partner_id.id or False,
                'related_crm_lead_id': self.id,
                'stage_id': stage_id,
                'phone': phone,
                'email': email,
            }
            cs = CustomerSuccess.create(vals)

        # open the found/created record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Success',
            'view_mode': 'form',
            'res_model': 'customer.success',
            'res_id': cs.id,
            'target': 'current',
            'context': dict(self.env.context, from_crm_lead_id=self.id),
        }


    def write(self, vals):
        # store previous stage ids so we can detect transitions
        old_stage_map = {rec.id: rec.stage_id.id if rec.stage_id else False for rec in self}
        res = super().write(vals)


        if 'create_cs' in vals and vals.get('create_cs') == 'yes':
            for rec in self:
                try:

                    rec.action_set_won()
                except Exception:

                    Stage = self.env['crm.stage']

                    won_stage = Stage.search([('probability', '>=', 100)], limit=1)
                    if not won_stage:
                        won_stage = Stage.search([('name', 'ilike', 'won')], limit=1)
                    if not won_stage:
                        won_stage = Stage.search([('name', 'ilike', 'achieved')], limit=1)
                    if won_stage:

                        try:
                            rec.write({'stage_id': won_stage.id})
                        except Exception:

                            try:
                                rec.sudo().write({'stage_id': won_stage.id})
                            except Exception:

                                pass

        if 'stage_id' in vals or 'probability' in vals:
            CustomerSuccess = self.env['customer.success']
            initial_stage = self._get_customer_success_initial_stage()
            cs_stage_id = initial_stage.id if initial_stage else False
            to_create = []
            for rec in self:
                old_stage = old_stage_map.get(rec.id)
                new_stage = rec.stage_id.id if rec.stage_id else False

                if old_stage == new_stage:
                    continue

                # Determine whether old/new are won
                old_stage_record = self.env['crm.stage'].browse(old_stage) if old_stage else False
                was_won_before = self._is_won_stage(old_stage_record)
                is_won_now = self._is_won_stage(rec.stage_id)


                if is_won_now and not was_won_before:
                    cs = CustomerSuccess.search([('related_crm_lead_id', '=', rec.id)], limit=1)
                    if cs:

                        activity_user_id = False
                        if hasattr(cs, 'assigned_user_id') and cs.assigned_user_id:
                            activity_user_id = cs.assigned_user_id.id
                        elif hasattr(rec, 'user_id') and rec.user_id:
                            activity_user_id = rec.user_id.id
                        else:
                            activity_user_id = self.env.uid

                        # compute a deadline (today + 1 day)
                        today_str = fields.Date.context_today(self)
                        try:
                            today_date = fields.Date.from_string(today_str)
                        except Exception:
                            from datetime import date
                            today_date = date.today()
                        deadline_date = today_date + timedelta(days=1)
                        deadline_str = fields.Date.to_string(deadline_date)

                        # resolve ir.model and activity type
                        ir_model = self.env['ir.model'].search([('model', '=', 'customer.success')], limit=1)
                        res_model_id = ir_model.id if ir_model else False
                        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                        activity_type_id = activity_type.id if activity_type else False

                        summary = "CRM Lead returned to Won stage"
                        note = "The CRM lead '%s' (id: %s) has been moved back to a Won stage in CRM. Please review." % (
                            rec.name or 'n/a', rec.id)

                        if not res_model_id or not activity_type_id:
                            fallback_msg = "Notice: couldn't create mail.activity (missing metadata). Original notice: %s" % (note,)
                            cs.message_post(body=fallback_msg, subject=summary, message_type='comment', subtype='mail.mt_note')
                        else:
                            activity_vals = {
                                'res_model': 'customer.success',
                                'res_model_id': res_model_id,
                                'res_id': cs.id,
                                'activity_type_id': activity_type_id,
                                'summary': summary,
                                'note': note,
                                'user_id': activity_user_id,
                                'date_deadline': deadline_str,
                            }
                            try:
                                self.env['mail.activity'].create(activity_vals)
                            except Exception as e:
                                err_msg = "Failed to create mail.activity: %s\nOriginal notice: %s" % (tools.ustr(e), note)
                                cs.message_post(body=err_msg, subject=summary, message_type='comment', subtype='mail.mt_note')
                    else:
                        # no CS exists -> preserve prior behavior: prepare to create a new CustomerSuccess record
                        phone, email = self._lead_phone_email(rec)
                        vals_cs = {
                            'name': rec.name or ('Customer Success for: %s' % (rec.id,)),
                            'partner_id': rec.partner_id.id or False,
                            'related_crm_lead_id': rec.id,
                            'stage_id': cs_stage_id,
                            'phone': phone,
                            'email': email,
                        }
                        to_create.append(vals_cs)

                # 3) Transition OUT OF Won -> create a warning activity in Customer Success
                if was_won_before and not is_won_now:
                    cs = CustomerSuccess.search([('related_crm_lead_id', '=', rec.id)], limit=1)
                    if not cs:
                        phone, email = self._lead_phone_email(rec)
                        cs_vals = {
                            'name': rec.name or ('Customer Success for: %s' % (rec.id,)),
                            'partner_id': rec.partner_id.id or False,
                            'related_crm_lead_id': rec.id,
                            'stage_id': cs_stage_id,
                            'phone': phone,
                            'email': email,
                        }
                        cs = CustomerSuccess.create(cs_vals)

                    activity_user_id = False
                    if hasattr(cs, 'assigned_user_id') and cs.assigned_user_id:
                        activity_user_id = cs.assigned_user_id.id
                    elif hasattr(rec, 'user_id') and rec.user_id:
                        activity_user_id = rec.user_id.id
                    else:
                        activity_user_id = self.env.uid

                    today_str = fields.Date.context_today(self)
                    try:
                        today_date = fields.Date.from_string(today_str)
                    except Exception:
                        from datetime import date
                        today_date = date.today()
                    deadline_date = today_date + timedelta(days=1)
                    deadline_str = fields.Date.to_string(deadline_date)

                    ir_model = self.env['ir.model'].search([('model', '=', 'customer.success')], limit=1)
                    res_model_id = ir_model.id if ir_model else False
                    activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                    activity_type_id = activity_type.id if activity_type else False

                    warning_summary = "Warning: Lead removed from Won stage in CRM"
                    warning_note = "The lead '%s' (id: %s) was moved out of a Won stage in CRM. Please review." % (
                        rec.name or 'n/a', rec.id)

                    if not res_model_id or not activity_type_id:
                        fallback_msg = (
                            "Warning: couldn't create mail.activity (missing res_model_id or activity_type). "
                            "Original warning: %s" % (warning_note,))
                        if cs:
                            cs.message_post(body=fallback_msg, subject=warning_summary, message_type='comment', subtype='mail.mt_note')
                        else:
                            rec.message_post(body=fallback_msg, subject=warning_summary, message_type='comment', subtype='mail.mt_note')
                    else:
                        activity_vals = {
                            'res_model': 'customer.success',
                            'res_model_id': res_model_id,
                            'res_id': cs.id,
                            'activity_type_id': activity_type_id,
                            'summary': warning_summary,
                            'note': warning_note,
                            'user_id': activity_user_id,
                            'date_deadline': deadline_str,
                        }
                        try:
                            self.env['mail.activity'].create(activity_vals)
                        except Exception as e:
                            err_msg = "Failed to create mail.activity: %s\nOriginal warning: %s" % (tools.ustr(e), warning_note)
                            if cs:
                                cs.message_post(body=err_msg, subject=warning_summary, message_type='comment', subtype='mail.mt_note')
                            else:
                                rec.message_post(body=err_msg, subject=warning_summary, message_type='comment', subtype='mail.mt_note')


            if to_create:
                CustomerSuccess.create(to_create)

        return res


