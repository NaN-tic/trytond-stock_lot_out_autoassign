# This file is part of the stock_lot_out_autoassign module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import doctest_setup, doctest_teardown
from trytond.tests.test_tryton import doctest_checker


class StockLotOutAutoassignTestCase(ModuleTestCase):
    'Test Stock Lot Out Autoassign module'
    module = 'stock_lot_out_autoassign'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockLotOutAutoassignTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_stock_shipment_out.rst',
            setUp=doctest_setup, tearDown=doctest_teardown, encoding='utf-8',
            checker=doctest_checker,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
