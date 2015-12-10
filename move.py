# This file is part stock_lot_out_autoassign module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from collections import OrderedDict

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

        if not moves:
            return super(Move, cls).assign_try(moves,
                with_childs=with_childs, grouping=grouping)

        configuration = Configuration(1)
        lot_priority = configuration.lot_priority or 'lot_date'
        today = Date.today()
        new_moves = []
        to_update = []
        lots_to_update = []
        product_ids = [m.product.id for m in moves]
        location_ids = set([m.from_location.id for m in moves])

        ctx = {
            'stock_date_end': today,
            'stock_assign': True,
            'forecast': False,
            }
        domain = [
            ('product', 'in', product_ids),
            ('quantity', '>', 0.0),
            ]
        if hasattr(Lot, 'expired'):
            domain.append(('expired', '=', False))

        for location_id in location_ids:
            ctx['locations'] = [location_id]
            with Transaction().set_context(ctx):
                lots = Lot.search(domain, order=[(lot_priority, 'ASC')])

            product_by_lots = OrderedDict(
                ((l.product.id, l.id), l.quantity) for l in lots)
            if not product_by_lots:
                continue

            for move in moves:
                if move.from_location.id != location_id:
                    continue
                if (not move.lot and move.product.lot_is_required(
                            move.from_location, move.to_location)):
                    remainder = move.internal_quantity
                    product = move.product
                    lots = [{'id': p[1], 'quantity': product_by_lots[p]}
                        for p in product_by_lots
                        if p[0] == product.id and product_by_lots[p]]
                    while lots and remainder > 0.0:
                        lot = lots[0]
                        assigned_quantity = min(lot['quantity'], remainder)
                        quantity = Uom.compute_qty(
                            move.product.default_uom, assigned_quantity,
                            move.uom)
                        if assigned_quantity == remainder:
                            values = {
                                'quantity': quantity,
                                'lot': lot['id'],
                                }
                            to_update.extend(([move], values))
                        else:
                            values = {
                                name: getattr(move, name)
                                    if (getattr(getattr(cls, name), '_type',
                                            False) not in ('reference',
                                            'many2one', 'one2many', 'many2many'
                                            ))
                                    else
                                        getattr(getattr(move, name), 'id', None
                                        )
                                    if (getattr(getattr(cls, name), '_type',
                                            False) != 'reference')
                                    else
                                        '%s,%s' % (getattr(getattr(move, name),
                                            '__name__'),
                                            getattr(getattr(move, name), 'id'))
                                    for name in cls._fields
                                    if getattr(move, name, False)
                                        and name != 'id'
                                        and (getattr(getattr(cls, name),
                                                '_type', False) != 'function')
                                }
                            values['quantity'] = quantity
                            values['lot'] = lot['id']
                            new_moves.append(values)
                            lots.pop(0)
                        lot['quantity'] -= assigned_quantity
                        if lot['quantity'] <= 0:
                            lots_to_update.append(Lot(lot['id']))
                        remainder -= assigned_quantity
                        product_by_lots[(product.id, lot['id'])] -= (
                            assigned_quantity)
                    if not lots:
                        to_update.extend(([move], {'quantity': Uom.compute_qty(
                            move.product.default_uom, remainder, move.uom)}))

        if to_update:
            cls.write(*to_update)
        if new_moves:
            new_moves = cls.create(new_moves)
        if lots_to_update:
            Lot.write(lots_to_update, {'active': False})

        return super(Move, cls).assign_try(new_moves + moves,
            with_childs=with_childs, grouping=grouping)
