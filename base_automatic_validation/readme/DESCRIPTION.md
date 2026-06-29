Abstract mixin to implement automatic validation rules on any Odoo model.

Inherit ``base.automatic.validation`` and configure rules via
``automatic.validation.rule`` to track a ``validation_status``
(``complete`` / ``incomplete``) on records.

Rules are evaluated automatically when configured trigger fields change,
or explicitly by calling ``detect_incomplete_rules()``.

**Three check types**

*By Domain* — the record must match an Odoo domain:

```
Model: event.registration
Domain: [('attendee_partner_id.phone', '!=', False)]
```

*Execute Code* — Python code sets ``result = True`` if the record is valid:

```python
result = bool(record.partner_id.email)
```

*By Method* — calls a method defined on the model that returns the
failing records as a recordset. Useful for batch checks that need
optimized SQL queries:

```python
# on event.registration
def check_has_partner(self):
    return self.filtered(lambda r: not r.attendee_partner_id)
```

**Multicompany**

Each rule has an optional ``company_id``. Leave it empty to apply the
rule to all companies. When set, the rule only applies to records
belonging to that company.

**How to use**

Inherit the mixin on your model:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "base.automatic.validation"]

    def _get_validation_trigger_fields(self):
        return ["state", "partner_id"]
```

Then create rules via *Settings > Automatic Validation > Validation Rules*
and select your model in the *Apply On* field.

**Extending with new models**

Add your model to the *Apply On* selection:

```python
class AutomaticValidationRule(models.Model):
    _inherit = "automatic.validation.rule"
    _name = "automatic.validation.rule"

    model = fields.Selection(
        selection_add=[("my.model", "My Model")],
        ondelete={"my.model": "cascade"},
    )
```
