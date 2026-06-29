# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr

_logger = logging.getLogger(__name__)


class AutomaticValidationRule(models.Model):
    _name = "automatic.validation.rule"
    _description = "Automatic Validation Rule"
    _order = "active desc, sequence asc"

    DEFAULT_PYTHON_CODE = """# Available variables:
#  - env: environment
#  - record: record being validated
#  - result: set to True if validation passes (False by default)
#  - datetime, date: useful Python libraries
# Example:
#  result = bool(record.partner_id.email)
"""

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(help="Gives the sequence order when applying the test.")
    model = fields.Selection(selection=[], string="Apply On", required=True)
    check_type = fields.Selection(
        [
            ("by_domain", "By Domain"),
            ("by_py_code", "Execute Code"),
            ("by_method", "By Method"),
        ],
        required=True,
        default="by_domain",
        help="By Domain: use an Odoo domain to check the condition.\n"
        "Execute Code: write Python code, set result=True if valid.\n"
        "By Method: call a method defined on the model.",
    )
    method = fields.Selection(selection=[], readonly=True)
    domain = fields.Char(default="[]")
    code = fields.Text(default=DEFAULT_PYTHON_CODE)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        help="Leave empty to apply to all companies.",
    )

    @api.constrains("check_type", "domain", "code", "model")
    def _check_rule_consistency(self):
        for rule in self:
            if rule.check_type == "by_py_code" and not rule.code:
                raise ValidationError(
                    _("Python code is missing on rule '%s'.", rule.name)
                )
            if rule.check_type == "by_domain" and not rule.domain:
                raise ValidationError(_("Domain is missing on rule '%s'.", rule.name))
            if rule.check_type == "by_method" and not rule.method:
                raise ValidationError(_("Method is missing on rule '%s'.", rule.name))

    @api.constrains("code")
    def _check_python_code(self):
        for rule in self.sudo().filtered("code"):
            msg = test_python_expr(expr=rule.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _get_domain(self):
        self.ensure_one()
        return safe_eval(self.domain)

    def _get_rules_info_for_domain(self, domain):
        return self._get_cached_rules_for_domain(tuple(domain))

    @api.model
    @tools.ormcache_context("domain", keys=("lang",))
    def _get_cached_rules_for_domain(self, domain):
        return [
            type("RuleInfo", (), r._to_cache_entry()) for r in self.search(list(domain))
        ]

    def _to_cache_entry(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "check_type": self.check_type,
            "domain": self._get_domain() if self.check_type == "by_domain" else None,
            "code": self.code,
            "method": self.method,
        }

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self.env.registry.clear_cache()
        return res

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res
