# This file is part stock_lot_out_autoassign module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Move']
__metaclass__ = PoolMeta


class Move:
    __name__ = 'stock.move'

    @classmethod
    def assign_try(cls, moves, with_childs=True, grouping=('product',)):
        '''
        If lots required assign lots in lot priority before assigning move.
        '''
        pool = Pool()
        Uom = pool.get('product.uom')
        Lot = pool.get('stock.lot')
        Date = pool.get('ir.date')
        Configuration = pool.get('stock.configuration')

        configuration = Configuration(1)
        lot_priority = configuration.lot_priority or 'lot_date'

        today = Date.today()
        new_moves = []
        lots_by_product = {}
        consumed_quantities = {}
        to_update = []
        products = [m.product.id for m in moves]
        locations = [m.from_location.id for m in moves]
        ctx = {
            'stock_date_end': today,
            'stock_assign': True,
            'forecast': False,
            'locations': locations,
            }
        with Transaction().set_context(ctx):
            lots = Lot.search([
                    ('product', 'in', products),
                    ('quantity', '>', 0.0),
                    ], order=[(lot_priority, 'ASC')])
        for lot in lots:
            product_id = lot.product.id
            if product_id not in lots_by_product:
                lots_by_product[product_id] = [lot]
            else:
                lots_by_product[product_id].append(lot)

        for move in moves:
            if (not move.lot and move.product.lot_is_required(
                        move.from_location, move.to_location)):

                lots = lots_by_product[move.product.id]
                remainder = move.internal_quantity
                while lots and remainder > 0.0:
                    lot = lots.pop(0)
                    consumed_quantities.setdefault(lot.id, 0.0)
                    lot_quantity = lot.quantity - consumed_quantities[lot.id]
                    assigned_quantity = min(lot_quantity, remainder)
                    if assigned_quantity == remainder:
                        values = {
                            'quantity': Uom.compute_qty(
                                move.product.default_uom, assigned_quantity,
                                move.uom),
                            'lot': lot,
                            }
                        to_update.extend(([move], values))
                        lots.insert(0, lot)
                    else:
                        quantity = Uom.compute_qty(
                            move.product.default_uom, assigned_quantity,
                            move.uom)
                        new_moves.extend(cls.copy([move], {
                                    'lot': lot.id,
                                    'quantity': quantity,
                                    }))

                    consumed_quantities[lot.id] += assigned_quantity
                    remainder -= assigned_quantity
                if not lots:
                    move.quantity = Uom.compute_qty(move.product.default_uom,
                        remainder, move.uom)
                    move.save()
                lots_by_product[move.product.id] = lots

        if to_update:
            cls.write(*to_update)

        return super(Move, cls).assign_try(new_moves + moves,
            with_childs=with_childs, grouping=grouping)
