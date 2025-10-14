from odoo import models, fields, api, _


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    # 1. Add the new field
    custom_survey_id = fields.Many2one(
        'survey.survey',
        string='Survey Template',
        help="Select the survey you want to send.",
        # If the action passes a default_survey_id, it will populate this field
        default=lambda self: self.env.context.get('default_survey_id') or self.env.context.get(
            'active_id') if self.env.context.get('active_model') == 'survey.survey' else False
    )

    customer_success_id = fields.Many2one(
        'customer.success',
        string='Customer Success',
        # Get the active record ID from the context when the wizard opens
        default=lambda self: self.env.context.get('active_id') if self.env.context.get('active_model') == 'customer.success' else False
    )

    # 2. Override create to use the custom_survey_id if available
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('custom_survey_id') and not vals.get('survey_id'):
                # Ensure the original survey_id field is set to the custom one before creation
                vals['survey_id'] = vals['custom_survey_id']
        return super().create(vals_list)

    # 3. Fix the onchange method to avoid non-existent function call
    @api.onchange('custom_survey_id')
    def _onchange_custom_survey_id(self):
        if self.custom_survey_id:
            # Update the original survey_id field (use .id for Odoo ORM when assigning Many2one value)
            self.survey_id = self.custom_survey_id.id

            # Update the subject dynamically
            self.subject = _("Participate to %s") % self.custom_survey_id.title
        else:
            # FIX: Instead of calling _get_default_subject(), set it to False/empty string
            self.subject = False
            self.survey_id = False

    # NOTE: The fields 'subject' and 'body' are already in survey.invite.
    # The 'survey_link' is a computed field that depends on 'survey_id' (now linked to custom_survey_id).


    @api.depends('survey_id')
    def _compute_share_link(self):
        # Call the original method first
        super()._compute_share_link()

        # Then, append our custom parameter to the link
        for invite in self:
            if invite.customer_success_id and invite.share_link:
                # Add the project ID as a URL parameter (e.g., &cs_id=123)
                invite.share_link = f"{invite.share_link}&cs_id={invite.customer_success_id.id}"