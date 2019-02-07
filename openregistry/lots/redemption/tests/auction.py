# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openregistry.lots.core.tests.base import snitch

from openregistry.lots.bargain.tests.base import (
    LotContentWebTest
)
from openregistry.lots.bargain.tests.json_data import auction_common
from openregistry.lots.bargain.tests.blanks.auction_blanks import (
    patch_auction,
    procurementMethodDetails_check_with_sandbox,
    procurementMethodDetails_check_without_sandbox,
    patch_auctions_with_lot,
    patch_auction_by_concierge,
)


class LotAuctionResourceTest(LotContentWebTest):
    initial_auction_data = deepcopy(auction_common)
    initial_status = 'draft'

    test_patch_auctions_with_lot = snitch(patch_auctions_with_lot)
    test_patch_auction_by_concierge = snitch(patch_auction_by_concierge)
    test_patch_auction = snitch(patch_auction)
    test_procurementMethodDetails_check_with_sandbox = snitch(procurementMethodDetails_check_with_sandbox)
    test_procurementMethodDetails_check_without_sandbox = snitch(procurementMethodDetails_check_without_sandbox)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LotAuctionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
