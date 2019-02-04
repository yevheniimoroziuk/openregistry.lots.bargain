# -*- coding: utf-8 -*-

import unittest

from openregistry.lots.redemption.tests import lot, document, item


def suite():
    tests = unittest.TestSuite()
    tests.addTest(document.suite())  # TODO: find out where tests interfere between each other
    tests.addTest(lot.suite())
    tests.addTest(item.suite())
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
