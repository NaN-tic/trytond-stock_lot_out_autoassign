#This file is part stock_lot_out_autoassign module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .move import *


def register():
    Pool.register(
        Configuration,
        Move,
        module='stock_lot_out_autoassign', type_='model')

