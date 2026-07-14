from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FreightShipment(models.Model):
    _name = 'freight.shipment'
    _description = 'Shipment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Reference', required=True, readonly=True, copy=False,
        default=lambda self: _('New'), index=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, tracking=True)
    shipment_type_id = fields.Many2one(
        'freight.shipment.type', string='Shipment Type', required=True,
        tracking=True, ondelete='restrict')
    origin = fields.Char(required=True, tracking=True)
    destination = fields.Char(required=True, tracking=True)
    pickup_date = fields.Date(
        string='Requested Pickup Date', required=True, tracking=True)
    delivery_date = fields.Date(
        string='Requested Delivery Date', required=True, tracking=True)
    state = fields.Selection(
        selection=[
            ('preparing', 'Preparing'),
            ('with_courier', 'With Courier'),
            ('on_the_way', 'On the Way'),
            ('delivered', 'Delivered'),
        ],
        string='Status', default='preparing', required=True, copy=False,
        readonly=True, index=True, tracking=True, group_expand=True)
    cargo_line_ids = fields.One2many(
        'freight.cargo.line', 'shipment_id', string='Cargo Items', copy=True)
    total_weight = fields.Float(
        string='Total Weight (kg)', compute='_compute_totals', store=True)
    total_volume = fields.Float(
        string='Total Volume (m³)', compute='_compute_totals', store=True,
        digits=(12, 3))
    note = fields.Text(string='Internal Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'freight.shipment') or _('New')
        return super().create(vals_list)

    @api.depends('cargo_line_ids.total_weight', 'cargo_line_ids.total_volume')
    def _compute_totals(self):
        for shipment in self:
            shipment.total_weight = sum(shipment.cargo_line_ids.mapped('total_weight'))
            shipment.total_volume = sum(shipment.cargo_line_ids.mapped('total_volume'))

    @api.constrains('pickup_date', 'delivery_date')
    def _check_dates(self):
        for shipment in self:
            if shipment.pickup_date and shipment.delivery_date \
                    and shipment.delivery_date < shipment.pickup_date:
                raise ValidationError(_(
                    "The requested delivery date of %(name)s cannot be earlier "
                    "than the requested pickup date.", name=shipment.name))

    def _advance_state(self, expected_state, new_state):
        """Move shipments one step forward, guarding against invalid jumps."""
        state_labels = dict(self._fields['state']._description_selection(self.env))
        for shipment in self:
            if shipment.state != expected_state:
                raise UserError(_(
                    "%(name)s cannot be moved to \"%(new_state)s\": it is in the "
                    "\"%(current_state)s\" stage, and this action only applies to "
                    "shipments in the \"%(expected_state)s\" stage.",
                    name=shipment.name,
                    new_state=state_labels[new_state],
                    current_state=state_labels[shipment.state],
                    expected_state=state_labels[expected_state]))
        self.write({'state': new_state})

    def action_hand_to_courier(self):
        for shipment in self:
            if not shipment.cargo_line_ids:
                raise UserError(_(
                    "%(name)s has no cargo items yet. Please add at least one "
                    "cargo item before handing the shipment to the courier.",
                    name=shipment.name))
        self._advance_state('preparing', 'with_courier')

    def action_start_delivery(self):
        self._advance_state('with_courier', 'on_the_way')

    def action_mark_delivered(self):
        self._advance_state('on_the_way', 'delivered')
