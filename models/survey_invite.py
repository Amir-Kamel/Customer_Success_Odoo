from odoo import models, fields, api, _


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'


    custom_survey_id = fields.Many2one(
        'survey.survey',
        string='Survey Template',
        help="Select the survey you want to send.",

        default=lambda self: self.env.context.get('default_survey_id') or self.env.context.get(
            'active_id') if self.env.context.get('active_model') == 'survey.survey' else False
    )

    customer_success_id = fields.Many2one(
        'customer.success',
        string='Customer Success',

        default=lambda self: self.env.context.get('active_id') if self.env.context.get('active_model') == 'customer.success' else False
    )

    # 2. Override create to use the custom_survey_id if available
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('custom_survey_id') and not vals.get('survey_id'):

                vals['survey_id'] = vals['custom_survey_id']
        return super().create(vals_list)


    @api.onchange('custom_survey_id')
    def _onchange_custom_survey_id(self):
        if self.custom_survey_id:

            self.survey_id = self.custom_survey_id.id

            self.subject = _("Participate to %s") % self.custom_survey_id.title
        else:

            self.subject = False
            self.survey_id = False


    @api.depends('survey_id')
    def _compute_share_link(self):
        super()._compute_share_link()


    def _get_answers_values(self):
        vals = super()._get_answers_values()

        if self.customer_success_id:
            vals['customer_success_id'] = self.customer_success_id.id

        return vals