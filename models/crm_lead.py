from odoo import models,fields
from datetime import timedelta
from odoo import tools


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def _get_customer_success_stage(self):
        stage_record = self.env.ref('Customer_Success.customer_success_stage_achieved', raise_if_not_found=False)
        if not stage_record:
            stage_model = self.env['customer.success.stage']
            stage_record = stage_model.search([('name', '=', 'Achieved')], limit=1)
            if not stage_record:
                stage_record = stage_model.create({'name': 'Achieved'})
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

    def write(self, vals):
        old_stage_map = {rec.id: rec.stage_id.id if rec.stage_id else False for rec in self}
        res = super().write(vals)

        # respond to changes in stage/probability
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

                if self._is_won_stage(rec.stage_id):
                    exists = CustomerSuccess.search([('related_crm_lead_id', '=', rec.id)], limit=1)
                    if exists:
                        continue

                    phone, email = self._lead_phone_email(rec)

                    vals_cs = {
                        'name': rec.name or ('Customer Success for: %s' % (rec.id,)),
                        'partner_id': rec.partner_id.id,
                        'related_crm_lead_id': rec.id,
                        'stage_id': cs_stage_id,
                        'phone': phone,
                        'email': email,
                    }
                    to_create.append(vals_cs)
            if to_create:
                CustomerSuccess.create(to_create)

        return res

    def write(self, vals):
        # store previous stage ids so we can detect transitions
        old_stage_map = {rec.id: rec.stage_id.id if rec.stage_id else False for rec in self}
        res = super().write(vals)

        # respond to changes in stage/probability
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

                # If the new stage is a "won" stage: ensure a CustomerSuccess record exists (existing logic)
                if self._is_won_stage(rec.stage_id):
                    exists = CustomerSuccess.search([('related_crm_lead_id', '=', rec.id)], limit=1)
                    if exists:
                        continue

                    phone, email = self._lead_phone_email(rec)

                    vals_cs = {
                        'name': rec.name or ('Customer Success for: %s' % (rec.id,)),
                        'partner_id': rec.partner_id.id,
                        'related_crm_lead_id': rec.id,
                        'stage_id': cs_stage_id,
                        'phone': phone,
                        'email': email,
                    }
                    to_create.append(vals_cs)

                # NEW: if we moved OUT of a won stage -> create a warning activity in Customer Success
                # Determine whether the old stage was won and the new stage is NOT won
                old_stage_record = self.env['crm.stage'].browse(old_stage) if old_stage else False
                was_won_before = self._is_won_stage(old_stage_record)
                is_won_now = self._is_won_stage(rec.stage_id)

                if was_won_before and not is_won_now:
                    # find or create Customer Success record to attach the warning to
                    cs = CustomerSuccess.search([('related_crm_lead_id', '=', rec.id)], limit=1)
                    if not cs:
                        # create a minimal CS record so the warning appears in the Customer Success module
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

                    # pick an activity user: prefer cs.user_id, fallback to lead salesperson, fallback to current user
                    activity_user_id = False
                    if hasattr(cs, 'user_id') and cs.user_id:
                        activity_user_id = cs.user_id.id
                    elif hasattr(rec, 'user_id') and rec.user_id:
                        activity_user_id = rec.user_id.id
                    else:
                        activity_user_id = self.env.uid

                    # compute deadline safely (today + 1)
                    today_str = fields.Date.context_today(self)  # 'YYYY-MM-DD'
                    today_date = fields.Date.from_string(today_str)  # datetime.date
                    deadline_date = today_date + timedelta(days=1)
                    deadline_str = fields.Date.to_string(deadline_date)  # 'YYYY-MM-DD'

                    # try to resolve ir.model for customer.success
                    ir_model = self.env['ir.model'].search([('model', '=', 'customer.success')], limit=1)
                    res_model_id = ir_model.id if ir_model else False

                    # try to get a To-Do activity type
                    activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                    activity_type_id = activity_type.id if activity_type else False

                    # create the warning activity with the lead name included
                    warning_summary = "Warning: Lead removed from Won stage in CRM"
                    warning_note = "The lead '%s' (id: %s) was moved out of a Won stage in CRM. Please review." % (
                        rec.name or 'n/a', rec.id)

                    if not res_model_id or not activity_type_id:
                        # fallback: post an internal chatter message to avoid breaking the write
                        fallback_msg = (
                                    "Warning: couldn't create mail.activity (missing res_model_id or activity_type). "
                                    "Original warning: %s" % (warning_note,))
                        # post on the customer.success record if available, else on the lead
                        if cs:
                            cs.message_post(body=fallback_msg, subject=warning_summary, message_type='comment',
                                            subtype='mail.mt_note')
                        else:
                            rec.message_post(body=fallback_msg, subject=warning_summary, message_type='comment',
                                             subtype='mail.mt_note')
                    else:
                        activity_vals = {
                            'res_model': 'customer.success',
                            'res_model_id': res_model_id,  # required by DB constraints in some setups
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
                            # fallback to chatter message so we don't block the write
                            err_msg = "Failed to create mail.activity: %s\nOriginal warning: %s" % (
                            tools.ustr(e), warning_note)
                            if cs:
                                cs.message_post(body=err_msg, subject=warning_summary, message_type='comment',
                                                subtype='mail.mt_note')
                            else:
                                rec.message_post(body=err_msg, subject=warning_summary, message_type='comment',
                                                 subtype='mail.mt_note')

            if to_create:
                CustomerSuccess.create(to_create)

        return res
