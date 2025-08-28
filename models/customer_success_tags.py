from odoo import models, fields
from random import randint

class CsmTag(models.Model):
    _name = "csm.tag"
    _description = "CSM Tag"

    COLOR_SELECTION = [
        ('0', 'Red'),
        ('1', 'Orange'),
        ('2', 'Yellow'),
        ('3', 'Green'),
        ('4', 'Blue'),
        ('5', 'Purple'),
        ('6', 'Pink'),
        ('7', 'Brown'),
    ]

    def _get_default_color(self):
        return str(randint(0, 7))

    name = fields.Char('Tag Name', required=True, translate=True)
    color = fields.Selection(
        COLOR_SELECTION,
        string="Color",
        default=_get_default_color
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Tag name already exists!"),
    ]
