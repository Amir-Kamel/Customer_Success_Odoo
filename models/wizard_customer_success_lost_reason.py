from odoo import models, fields


class CustomerSuccessLostReasonWizard(models.TransientModel):
    _name = 'customer.success.lost.reason.wizard'
    _description = 'Lost Reason Wizard'

    # The reason chosen from predefined reasons
    reason = fields.Many2one(
        'customer.success.lost.reason',
        string="Reason",
        required=True
    )

    # The customer success record this wizard applies to
    customer_success_id = fields.Many2one(
        'customer.success',
        string="Customer Success",
        required=True
    )

    def action_confirm(self):
        """Apply the chosen reason and set stage = Lost"""
        self.ensure_one()
        if self.customer_success_id:
            # Get Lost stage
            lost_stage = self.env['customer.success.stage'].search([('name', '=', 'Lost')], limit=1)

            # Write changes to the record
            self.customer_success_id.write({
                'stage_id': lost_stage.id if lost_stage else False,
                'lost_reason_id': self.reason.id,
                'probability': 0,
            })

        # Close wizard
        return {'type': 'ir.actions.act_window_close'}
