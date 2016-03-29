# This file is part of the stock_lot_out_autoassign module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']


class Configuration:
    __metaclass__ = PoolMeta
    __name__ = 'stock.configuration'
    lot_priority = fields.Selection([
            ('lot_date', 'Date Lot'),
            ],
        'Lot Priority', required=True)

    @staticmethod
    def default_lot_priority():
        return 'lot_date'
