from odoo import models, fields, api
from odoo.exceptions import UserError

class CustomerSuccessStage(models.Model):
    _name = 'customer.success.stage'
    _description = 'Customer Success Stage'
    _order = 'sequence, id'

    name = fields.Char(string="Stage Name", required=True)
    sequence = fields.Integer(string="Sequence", default=1)
    fold = fields.Boolean(string="Folded in Kanban", help="If checked, this stage will be folded by default in the Kanban view.")


    is_won = fields.Boolean(string="Achieved")
    is_lost = fields.Boolean(string="Lost")



    # -----------------------------
    # Before create/write: ensure required name for Won/Lost
    # -----------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_won'):
                vals['name'] = 'Achieved'
            elif vals.get('is_lost'):
                vals['name'] = 'Lost'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('is_won'):
            vals['name'] = 'Achieved'
        elif vals.get('is_lost'):
            vals['name'] = 'Lost'
        return super().write(vals)



    # -----------------------------
    # Onchange to enforce single checkbox and dynamic name
    # -----------------------------
    @api.onchange('is_won', 'is_lost')
    def _onchange_stage_type(self):
        for stage in self:
            # Only one can be checked
            if stage.is_won and stage.is_lost:
                stage.is_won = False
                stage.is_lost = False
                return {
                    'warning': {
                        'title': "Invalid Selection",
                        'message': "You cannot select both Won and Lost at the same time."
                    }
                }

            # Set the name dynamically and readonly
            if stage.is_won:
                stage.name = "Achieved"
            elif stage.is_lost:
                stage.name = "Lost"
            # else: leave the name editable, user can remove checkboxes

    # -----------------------------
    # SQL or Python constraint to prevent multiple Won/Lost stages
    # -----------------------------
    @api.constrains('is_won', 'is_lost')
    def _check_unique_won_lost(self):
        for stage in self:
            if stage.is_won:
                existing_won = self.search([('is_won', '=', True), ('id', '!=', stage.id)])
                if existing_won:
                    raise UserError("There is already a stage marked as 'Achieved'. You cannot create another one.")
            if stage.is_lost:
                existing_lost = self.search([('is_lost', '=', True), ('id', '!=', stage.id)])
                if existing_lost:
                    raise UserError("There is already a stage marked as 'Lost'. You cannot create another one.")


    # -----------------------------
    # Constrain: Prevent manual Won/Lost in name
    # -----------------------------
    @api.constrains('name')
    def _prevent_manual_won_lost(self):
        for stage in self:
            if stage.name.strip().capitalize() in ['Achieved', 'Lost']:
                # If checkbox is not set but name is Won/Lost → block it
                if not stage.is_won and not stage.is_lost:
                    raise UserError("You cannot manually name a stage 'Achieved' or 'Lost'. Use the checkboxes instead.")

    # -----------------------------
    # Onchange: Capitalize first letter of each word
    # -----------------------------
    @api.onchange('name')
    def _onchange_name_capitalize(self):
        for stage in self:
            if stage.name:
                stage.name = " ".join([w.capitalize() for w in stage.name.split()])