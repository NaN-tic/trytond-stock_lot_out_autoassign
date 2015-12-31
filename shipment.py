# This file is part stock_lot_out_autoassign module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['ShipmentIn', 'ShipmentOut']
__metaclass__ = PoolMeta


class ShipmentIn:
    __name__ = 'stock.shipment.in'

    @classmethod
    def done(cls, shipments):
        Lot = Pool().get('stock.lot')

        lots_active = set()
        for s in shipments:
            for m in s.inventory_moves:
                if m.lot and not m.lot.active:
                    lots_active.add(m.lot)

        if lots_active:
            Lot.write(list(lots_active), {'active': True})

        return super(ShipmentIn, cls).done(shipments)


class ShipmentOut:
    __name__ = 'stock.shipment.out'

    @classmethod
    def assign_try(cls, shipments):
        pool = Pool()
        Move = pool.get('stock.move')

        moves = []
        for s in shipments:
            for move in s.inventory_moves:
                if (not move.lot and move.product.lot_is_required(
                            move.from_location, move.to_location)):
                    moves.append(move)

        if moves:
            Move.assign_lots(moves)

        return super(ShipmentOut, cls).assign_try(shipments)
