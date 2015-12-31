# This file is part stock_lot_out_autoassign module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['ShipmentOut']
__metaclass__ = PoolMeta


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
