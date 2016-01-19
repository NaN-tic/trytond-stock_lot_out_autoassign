===========================
Stock Shipment Out Scenario
===========================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()
    >>> yesterday = today - relativedelta(days=1)

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install stock Module::

    >>> Module = Model.get('ir.module')
    >>> module, = Module.find([('name', '=', 'stock_lot_out_autoassign')])
    >>> module.click('install')
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Get stock lot type::

    >>> LotType = Model.get('stock.lot.type')
    >>> supplier_lot_type, = LotType.find([('code', '=', 'supplier')])
    >>> customer_lot_type, = LotType.find([('code', '=', 'customer')])
    >>> storage_lot_type, = LotType.find([('code', '=', 'storage')])

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.cost_price = Decimal('8')
    >>> template.lot_required.append(supplier_lot_type)
    >>> template.lot_required.append(customer_lot_type)
    >>> template.lot_required.append(storage_lot_type)
    >>> template.save()
    >>> product.template = template
    >>> product.save()

Get stock locations::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])

Create Shipment Out::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment_out = ShipmentOut()
    >>> shipment_out.planned_date = today
    >>> shipment_out.customer = customer
    >>> shipment_out.warehouse = warehouse_loc
    >>> shipment_out.company = company

Add a shipment line::

    >>> StockMove = Model.get('stock.move')
    >>> move = StockMove()
    >>> move.product = product
    >>> move.uom =unit
    >>> move.quantity = 40
    >>> move.from_location = output_loc
    >>> move.to_location = customer_loc
    >>> move.company = company
    >>> move.unit_price = Decimal('1')
    >>> move.currency = company.currency
    >>> shipment_out.outgoing_moves.append(move)
    >>> shipment_out.save()

Set the shipment state to waiting::

    >>> shipment_out.click('wait')
    >>> shipment_out.reload()
    >>> len(shipment_out.outgoing_moves)
    1
    >>> len(shipment_out.inventory_moves)
    1

Create 2 Lots::

    >>> Lot = Model.get('stock.lot')
    >>> lot_1 = Lot()
    >>> lot_1.number = '1'
    >>> lot_1.product = product
    >>> lot_1.active = True
    >>> lot_1.save()
    >>> lot_2 = Lot()
    >>> lot_2.number = '2'
    >>> lot_2.product = product
    >>> lot_2.active = True
    >>> lot_2.save()

Make 30 units of the product available in 2 different lots::

    >>> for lot in (lot_1, lot_2):
    ...     incoming_move = StockMove()
    ...     incoming_move.product = product
    ...     incoming_move.uom = unit
    ...     incoming_move.quantity = 15
    ...     incoming_move.from_location = supplier_loc
    ...     incoming_move.to_location = storage_loc
    ...     incoming_move.planned_date = today
    ...     incoming_move.effective_date = today
    ...     incoming_move.company = company
    ...     incoming_move.unit_price = Decimal('1')
    ...     incoming_move.currency = company.currency
    ...     incoming_move.lot = lot
    ...     incoming_move.click('do')

Assign the shipment now::

    >>> shipment_out.click('assign_try')
    False
    >>> shipment_out.reload()
    >>> len(shipment_out.inventory_moves)
    3
    >>> len(shipment_out.outgoing_moves)
    1
    >>> moves = [m for m in shipment_out.inventory_moves if m.lot]
    >>> moves.sort()
    >>> for move in moves:
    ...     move.lot.number
    ...     move.quantity
    u'1'
    15.0
    u'2'
    15.0
