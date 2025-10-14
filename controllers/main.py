from odoo.http import request
from odoo.addons.survey.controllers.main import Survey


class SurveyCustom(Survey):

    def _prepare_survey_start(self, survey_access_token, answer_access_token, **post):
        # Check for our custom parameter in the URL
        customer_success_id = post.get('cs_id')

        # If found, set it in the request context before calling the super method
        if customer_success_id:
            try:
                # Inject the ID into the context as an integer
                request.update_context(customer_success_id=int(customer_success_id))
            except ValueError:
                # Handle non-integer values gracefully
                pass

        return super(SurveyCustom, self)._prepare_survey_start(survey_access_token, answer_access_token, **post)