from odoo import models, api

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
        keywords = ['won', 'Won', 'achieved', 'win']
        for k in keywords:
            if k in name:
                return True

        return False

    def action_set_won(self):

        res = super().action_set_won()

        CustomerSuccess = self.env['customer.success']
        stage_record = self._get_customer_success_stage()
        stage_id = stage_record.id if stage_record else False

        to_create = []
        for lead in self:

            exists = CustomerSuccess.search([('related_crm_lead_id', '=', lead.id)], limit=1)
            if exists:
                continue

            vals = {
                'name': lead.name or ('Customer Success for: %s' % (lead.id,)),
                'partner_id': lead.partner_id.id or False,
                'related_crm_lead_id': lead.id,
                'stage_id': stage_id,

            }
            to_create.append(vals)

        if to_create:
            CustomerSuccess.create(to_create)

        return res

    def write(self, vals):

        old_stage_map = {rec.id: rec.stage_id.id if rec.stage_id else False for rec in self}

        res = super().write(vals)


        if 'stage_id' in vals or 'probability' in vals:
            CustomerSuccess = self.env['customer.success']
            cs_stage = self._get_customer_success_stage()
            cs_stage_id = cs_stage.id if cs_stage else False
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
                    vals_cs = {
                        'name': rec.name or ('Customer Success for: %s' % (rec.id,)),
                        'partner_id': rec.partner_id.id or False,
                        'related_crm_lead_id': rec.id,
                        'stage_id': cs_stage_id,
                    }
                    to_create.append(vals_cs)
            if to_create:
                CustomerSuccess.create(to_create)

        return res
