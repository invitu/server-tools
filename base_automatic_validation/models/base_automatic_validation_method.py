# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from collections import defaultdict

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class BaseAutomaticValidationMethod(models.AbstractModel):
    _name = "base.automatic.validation.method"
    _description = "Automatic Validation Methods"

    def _get_main_records(self):
        """Return the records on which incomplete_rule_ids will be written.
        Override to write on a parent record instead of self (e.g. write on
        event.event when checking event.registration lines)."""
        return self

    def _rule_domain(self):
        return [("model", "=", self._name), ("active", "=", True)]

    def _get_base_domain(self):
        """Base domain applied before evaluating each rule.
        Override to restrict which records are checked."""
        return []

    def _get_incomplete_rules(self):
        """Return tuple (all_incomplete_ids, rules_to_remove, rules_to_add)."""
        rules_info = (
            self.env["automatic.validation.rule"]
            .sudo()
            ._get_rules_info_for_domain(self._rule_domain())
        )
        all_incomplete_ids = []
        main_records = self._get_main_records()
        rules_to_remove = defaultdict(main_records.browse)
        rules_to_add = defaultdict(main_records.browse)
        for rule_info in rules_info:
            records_with_rule = main_records.filtered(
                lambda r, rid=rule_info.id: rid in r.incomplete_rule_ids.ids
            )
            records_failing = self._check_rule(rule_info)
            to_remove = records_with_rule - records_failing
            to_add = records_failing - records_with_rule
            if to_remove:
                rules_to_remove[rule_info.id] |= to_remove
            if to_add:
                rules_to_add[rule_info.id] |= to_add
            if records_failing:
                all_incomplete_ids.append(rule_info.id)
        return all_incomplete_ids, rules_to_remove, rules_to_add

    def detect_incomplete_rules(self):
        """Evaluate all rules and update incomplete_rule_ids on records."""
        all_incomplete_ids, rules_to_remove, rules_to_add = self._get_incomplete_rules()
        for rule_id, records in rules_to_remove.items():
            records.write({"incomplete_rule_ids": [(3, rule_id)]})
        for rule_id, records in rules_to_add.items():
            records.write({"incomplete_rule_ids": [(4, rule_id)]})
        return all_incomplete_ids

    @api.model
    def _rule_eval_context(self, rec):
        return {
            "env": self.env,
            "record": rec,
            "result": False,
        }

    @api.model
    def _rule_eval(self, rule_info, rec):
        space = self._rule_eval_context(rec)
        try:
            safe_eval(rule_info.code, space, mode="exec", nocopy=True)
        except Exception as e:
            _logger.exception(e)
            raise UserError(
                _(
                    "Error in validation rule %(name)s:\n%(error)s",
                    name=rule_info.name,
                    error=e,
                )
            ) from e
        return not bool(space.get("result", False))

    def _check_rule(self, rule_info):
        """Return the records of self that FAIL the rule."""
        if rule_info.check_type == "by_py_code":
            return self._check_rule_by_py_code(rule_info)
        elif rule_info.check_type == "by_domain":
            return self._check_rule_by_domain(rule_info)
        elif rule_info.check_type == "by_method":
            return self._check_rule_by_method(rule_info)
        return self.browse()

    def _check_rule_by_py_code(self, rule_info):
        base_domain = self._get_base_domain()
        records = self.filtered_domain(base_domain) if base_domain else self
        failing = self.env[self._name]
        for record in records:
            if self._rule_eval(rule_info, record):
                failing |= record
        return failing

    def _check_rule_by_domain(self, rule_info):
        """Records that FAIL = records NOT matching the validation domain."""
        base_domain = self._get_base_domain()
        rule_domain = rule_info.domain
        if base_domain:
            full_domain = expression.AND([base_domain, rule_domain])
        else:
            full_domain = rule_domain
        passing = self.filtered_domain(full_domain)
        return self - passing

    def _check_rule_by_method(self, rule_info):
        """Call a method on the recordset — returns records that FAIL.
        The method must return the failing records as a recordset."""
        base_domain = self._get_base_domain()
        records = self.filtered_domain(base_domain) if base_domain else self
        return getattr(records, rule_info.method)()

    def _get_validation_trigger_fields(self):
        """Override to declare fields that trigger detect_incomplete_rules."""
        return []
