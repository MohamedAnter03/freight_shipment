{
    'name': 'Freight Shipment Management',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Register shipment requests, track their delivery lifecycle and print shipment orders',
    'description': """
Freight Shipment Management
===========================
A lightweight freight management module:

* Configurable shipment types (Road, Air, Ocean, Parcel, ...) with archiving.
* Shipment requests with a unique reference, customer, route and requested dates.
* Multiple cargo items per shipment with automatic weight / volume totals.
* Guided delivery lifecycle (Preparing -> With Courier -> On the Way -> Delivered)
  driven by buttons and fully tracked in the chatter.
* Shipment User / Shipment Manager roles.
* Printable PDF shipment order for the driver.
""",
    'author': 'Mohamed Anter',
    'license': 'LGPL-3',
    'depends': ['mail'],
    'data': [
        'security/freight_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/freight_shipment_report.xml',
        'report/freight_shipment_templates.xml',
        'views/freight_shipment_type_views.xml',
        'views/freight_shipment_views.xml',
        'views/freight_menus.xml',
    ],
    'demo': [
        'demo/freight_demo.xml',
    ],
    'application': True,
    'installable': True,
}
