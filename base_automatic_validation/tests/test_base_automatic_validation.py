# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_test_helper import FakeModelLoader

from odoo.tests.common import TransactionCase


class TestBaseAutomaticValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()
        from .validation_test_model import (
            AutomaticValidationRuleTest,
            AutomaticValidationTest,
        )

        self.loader.update_registry(
            (AutomaticValidationRuleTest, AutomaticValidationTest)
        )
        self.record = self.env["base.automatic.validation.test"].create(
            {"name": "Test Record", "value": 10}
        )
        self.rule_domain = self.env["automatic.validation.rule"].create(
            {
                "name": "Value must be positive",
                "model": "base.automatic.validation.test",
                "check_type": "by_domain",
                "domain": "[('value', '>', 0)]",
            }
        )
        self.rule_code = self.env["automatic.validation.rule"].create(
            {
                "name": "Name longer than 2 chars",
                "model": "base.automatic.validation.test",
                "check_type": "by_py_code",
                "code": "result = len(record.name or '') > 2",
            }
        )

    def tearDown(self):
        self.loader.restore_registry()
        super().tearDown()

    def test_rule_domain_passes(self):
        """Domain rule: record matching domain passes (not in failing set)."""
        failing = self.record._check_rule_by_domain(
            type(
                "R",
                (),
                {
                    "domain": [("value", ">", 0)],
                    "check_type": "by_domain",
                },
            )()
        )
        self.assertNotIn(self.record, failing)

    def test_rule_domain_fails(self):
        """Domain rule: record not matching domain is in failing set."""
        self.record.value = -1
        failing = self.record._check_rule_by_domain(
            type(
                "R",
                (),
                {
                    "domain": [("value", ">", 0)],
                    "check_type": "by_domain",
                },
            )()
        )
        self.assertIn(self.record, failing)

    def test_rule_code_passes(self):
        """Code rule passes when result=True."""
        self.assertFalse(
            self.record._rule_eval(
                type(
                    "R",
                    (),
                    {
                        "name": "test",
                        "code": "result = len(record.name or '') > 2",
                        "check_type": "by_py_code",
                    },
                )(),
                self.record,
            )
        )

    def test_rule_code_fails(self):
        """Code rule fails when result=False."""
        self.record.name = "AB"
        self.assertTrue(
            self.record._rule_eval(
                type(
                    "R",
                    (),
                    {
                        "name": "test",
                        "code": "result = len(record.name or '') > 2",
                        "check_type": "by_py_code",
                    },
                )(),
                self.record,
            )
        )

    def test_detect_incomplete_rules_complete(self):
        """detect_incomplete_rules sets complete when all rules pass."""
        self.record.detect_incomplete_rules()
        self.assertEqual(self.record.validation_status, "complete")
        self.assertFalse(self.record.incomplete_rule_ids)

    def test_detect_incomplete_rules_incomplete(self):
        """detect_incomplete_rules adds failing rule to incomplete_rule_ids."""
        self.record.value = -1
        self.record.detect_incomplete_rules()
        self.assertIn(self.rule_domain, self.record.incomplete_rule_ids)
        self.assertEqual(self.record.validation_status, "incomplete")

    def test_detect_incomplete_rules_clears_resolved(self):
        """detect_incomplete_rules removes rule when condition is fixed."""
        self.record.value = -1
        self.record.detect_incomplete_rules()
        self.assertIn(self.rule_domain, self.record.incomplete_rule_ids)
        self.record.value = 5
        self.record.detect_incomplete_rules()
        self.assertNotIn(self.rule_domain, self.record.incomplete_rule_ids)
        self.assertEqual(self.record.validation_status, "complete")

    def test_main_incomplete_rule_id(self):
        """main_incomplete_rule_id points to first incomplete rule."""
        self.record.value = -1
        self.record.detect_incomplete_rules()
        self.assertEqual(
            self.record.main_incomplete_rule_id,
            self.record.incomplete_rule_ids[0],
        )
