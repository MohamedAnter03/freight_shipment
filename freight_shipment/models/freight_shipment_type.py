from odoo import fields, models


class FreightShipmentType(models.Model):
    _name = 'freight.shipment.type'
    _description = 'Shipment Type'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Short internal code, e.g. ROAD, AIR.")
    category = fields.Selection(
        selection=[
            ('land', 'Land'),
            ('air', 'Air'),
            ('sea', 'Sea'),
            ('other', 'Other'),
        ],
        required=True,
        default='land',
        help="Transport family this type belongs to, used for grouping and reporting.",
    )
    active = fields.Boolean(default=True)
    shipment_count = fields.Integer(compute='_compute_shipment_count')

    _code_uniq = models.Constraint(
        'unique(code)',
        'The code of a shipment type must be unique.',
    )

    def _compute_shipment_count(self):
        counts = dict(self.env['freight.shipment']._read_group(
            domain=[('shipment_type_id', 'in', self.ids)],
            groupby=['shipment_type_id'],
            aggregates=['__count'],
        ))
        for shipment_type in self:
            shipment_type.shipment_count = counts.get(shipment_type, 0)

    def action_view_shipments(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'freight_shipment.action_freight_shipment')
        action['domain'] = [('shipment_type_id', '=', self.id)]
        action['context'] = {'default_shipment_type_id': self.id}
        return action
