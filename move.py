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
        Period = pool.get('stock.period')
        Lot = pool.get('stock.lot')
        Date = pool.get('ir.date')
        Configuration = pool.get('stock.configuration')
        cursor = Transaction().cursor

        configuration = Configuration(1)
        lot_priority = configuration.lot_priority or 'lot_date'

        period = None
        periods = Period.search([
                ('state', '=', 'closed'),
                ], order=[('date', 'DESC')], limit=1)
        if periods:
            period, = periods

        today = Date.today()
        new_moves = []
        to_update = []
        product_ids = [m.product.id for m in moves]
        location_ids = [m.from_location.id for m in moves]
        ctx = {
            'stock_date_end': today,
            'stock_assign': True,
            'forecast': False,
            'locations': location_ids,
            }
        with Transaction().set_context(ctx):
            lot_domain = [
                    ('product', 'in', product_ids),
                    ('quantity', '>', 0.0),
                    ]
            if period:
                lot_domain.append(('lot_date', '>', period.date))
            lots = Lot.search(lot_domain, order=[(lot_priority, 'ASC')])
        query = cls.compute_quantities_query(location_ids)
        cursor.execute(*query)
        quantities = cursor.fetchall()
        lots_by_product = {
            (q[0], q[1]): [[l, l.quantity]
                for l in lots
                if q[1] == l.product.id]
            for q in quantities if q[2] > 0.0 and q[1] in product_ids
            }

        for move in moves:
            if (not move.lot and move.product.lot_is_required(
                        move.from_location, move.to_location)):
                location = move.from_location
                product = move.product
                remainder = move.internal_quantity
                lots = lots_by_product.get((location.id, product.id), False)
                while lots and remainder > 0.0:
                    lot, lot_quantity = lots[0]
                    assigned_quantity = min(lot_quantity, remainder)
                    quantity = Uom.compute_qty(
                        move.product.default_uom, assigned_quantity,
                        move.uom)
                    if assigned_quantity == remainder:
                        values = {
                            'quantity': quantity,
                            'lot': lot,
                            }
                        to_update.extend(([move], values))
                        lots[0][1] -= assigned_quantity
                    else:
                        values = {
                            name: getattr(move, name)
                                if (getattr(getattr(cls, name), '_type', False
                                    ) not in ('reference',
                                        'many2one', 'one2many', 'many2many'))
                                else
                                    getattr(getattr(move, name), 'id', None)
                                if (getattr(getattr(cls, name), '_type', False
                                    ) != 'reference')
                                else
                                    '%s,%s' % (getattr(getattr(move, name),
                                        '__name__'),
                                        getattr(getattr(move, name), 'id'))
                                for name in cls._fields
                                if getattr(move, name, False)
                                    and name != 'id'
                                    and (getattr(getattr(cls, name), '_type',
                                            False) != 'function')
                            }
                        values['quantity'] = quantity
                        values['lot'] = lot
                        new_moves.append(values)
                        lots.pop(0)

                    remainder -= assigned_quantity
                if not lots:
                    move.quantity = Uom.compute_qty(move.product.default_uom,
                        remainder, move.uom)
                    move.save()
                lots_by_product[move.product.id] = lots

        if to_update:
            cls.write(*to_update)
        if new_moves:
            new_moves = cls.create(new_moves)

        return super(Move, cls).assign_try(new_moves + moves,
            with_childs=with_childs, grouping=grouping)
