from odoo import models

class CrmLead(models.Model):
    _inherit = "crm.lead"

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
