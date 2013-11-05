#This file is part stock_lot_out_autoassign module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import Workflow
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['ShipmentOut']
__metaclass__ = PoolMeta


class ShipmentOut:
    __name__ = 'stock.shipment.out'

    @classmethod
    @Workflow.transition('assigned')
    def assign(cls, shipments):
        pool = Pool()
        Lot = pool.get('stock.lot')
        Move = pool.get('stock.move')
        Location = pool.get('stock.location')
        Date = pool.get('ir.date')

        context = {}
        locations = Location.search([
                ('type', '=', 'storage'),
                ])
        context['locations'] = [l.id for l in locations]
        context['stock_date_end'] = Date.today()

        with Transaction().set_context(context):
            for shipment in shipments:
                for move in shipment.outgoing_moves:
                    if not move.lot and move.product.lot_is_required(
                        move.from_location, move.to_location):
                        rest = move.quantity
                        lots = Lot.search([
                                ('product', '=', move.product.id)
                                ])
                        for lot in lots:
                            stock_available = lot.forecast_quantity
                            if stock_available <= 0.0:
                                continue
                            if stock_available < rest:
                                rest -= stock_available
                                quantity = move.quantity - stock_available
                                if not quantity > 0:
                                    continue
                                Move.copy([move], default={
                                    'quantity': quantity,
                                    'lot': lot.id,
                                    })
                                Move.write([move], {'quantity': stock_available})
                            else:
                                Move.write([move], {'lot': lot.id})
                                break
        super(ShipmentOut, cls).assign(shipments)
