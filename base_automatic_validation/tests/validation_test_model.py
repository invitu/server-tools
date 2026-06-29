# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AutomaticValidationRuleTest(models.Model):
    _inherit = "automatic.validation.rule"
    _name = "automatic.validation.rule"

    model = fields.Selection(
        selection_add=[
            ("base.automatic.validation.test", "Validation Test"),
        ],
        ondelete={"base.automatic.validation.test": "cascade"},
    )


class AutomaticValidationTest(models.Model):
    _inherit = "base.automatic.validation"
    _name = "base.automatic.validation.test"
    _description = "Automatic Validation Test Model"

    name = fields.Char(required=True)
    value = fields.Integer()
