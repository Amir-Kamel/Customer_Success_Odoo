from odoo import fields, models

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    # 1. Field to link back to the Customer Success record
    customer_success_id = fields.Many2one(
        'customer.success',
        string='Source Project',
        readonly=True,
        ondelete='set null',
        help="The Customer Success project this survey was initiated from."
    )

    @models.api.model_create_multi
    def create(self, vals_list):
        # 1. Get the customer_success_id from the context (pushed by the controller)
        customer_success_id = self.env.context.get('customer_success_id')

        # 2. If the ID is found in the context, inject it into every response creation dictionary
        if customer_success_id:
            for vals in vals_list:
                vals['customer_success_id'] = customer_success_id

        # 3. Call the original create method
        return super(SurveyUserInput, self).create(vals_list)