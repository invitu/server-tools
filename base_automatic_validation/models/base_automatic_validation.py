# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class BaseAutomaticValidation(models.AbstractModel):
    _inherit = "base.automatic.validation.method"
    _name = "base.automatic.validation"
    _description = "Automatic Validation Mixin"

    _automatic_validation_company_field = "company_id"

    incomplete_rule_ids = fields.Many2many(
        "automatic.validation.rule",
        string="Incomplete Rules",
        copy=False,
    )
    main_incomplete_rule_id = fields.Many2one(
        "automatic.validation.rule",
        compute="_compute_main_incomplete_rule",
        store=True,
    )
    validation_status = fields.Selection(
        [("complete", "Complete"), ("incomplete", "Incomplete")],
        compute="_compute_validation_status",
        store=True,
    )

    @api.depends("incomplete_rule_ids")
    def _compute_main_incomplete_rule(self):
        for rec in self:
            rec.main_incomplete_rule_id = (
                rec.incomplete_rule_ids[0] if rec.incomplete_rule_ids else False
            )

    @api.depends("incomplete_rule_ids")
    def _compute_validation_status(self):
        for rec in self:
            rec.validation_status = (
                "incomplete" if rec.incomplete_rule_ids else "complete"
            )

    def _get_company(self):
        company_field = self._automatic_validation_company_field
        if self and company_field in self._fields and self[company_field]:
            return self[company_field]
        return self.env.company

    def _rule_domain(self):
        return [
            ("model", "=", self._name),
            ("active", "=", True),
            ("company_id", "in", [False] + self._get_company().ids),
        ]

    def write(self, vals):
        result = super().write(vals)
        trigger_fields = self._get_validation_trigger_fields()
        if trigger_fields and any(f in vals for f in trigger_fields):
            self.detect_incomplete_rules()
        return result
