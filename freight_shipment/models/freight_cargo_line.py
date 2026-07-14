from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FreightCargoLine(models.Model):
    _name = 'freight.cargo.line'
    _description = 'Shipment Cargo Item'

    shipment_id = fields.Many2one(
        'freight.shipment', required=True, ondelete='cascade', index=True)
    description = fields.Char(required=True)
    quantity = fields.Float(default=1.0, required=True)
    weight = fields.Float(
        string='Unit Weight (kg)', help="Weight of a single unit, in kg.")
    volume = fields.Float(
        string='Unit Volume (m³)', digits=(12, 3),
        help="Volume of a single unit, in cubic meters.")
    total_weight = fields.Float(
        compute='_compute_totals', store=True, string='Total Weight (kg)')
    total_volume = fields.Float(
        compute='_compute_totals', store=True, string='Total Volume (m³)',
        digits=(12, 3))

    @api.depends('quantity', 'weight', 'volume')
    def _compute_totals(self):
        for line in self:
            line.total_weight = line.quantity * line.weight
            line.total_volume = line.quantity * line.volume

    @api.constrains('quantity', 'weight', 'volume')
    def _check_positive_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_(
                    "The quantity of cargo item \"%(description)s\" must be "
                    "greater than zero.", description=line.description))
            if line.weight < 0 or line.volume < 0:
                raise ValidationError(_(
                    "The weight and volume of cargo item \"%(description)s\" "
                    "cannot be negative.", description=line.description))
