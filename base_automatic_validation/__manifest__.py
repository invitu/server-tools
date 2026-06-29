# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Base Automatic Validation",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "INVITU, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-tools",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/automatic_validation_rule_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
