# -*- coding: utf-8 -*-
import os
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP

from openregistry.lots.core.constants import (
    SANDBOX_MODE,
)
from openregistry.lots.core.tests.base import (
    connection_mock_config,
    BaseLotWebTest as BaseLWT,
    MOCK_CONFIG as BASE_MOCK_CONFIG
)
from openregistry.lots.redemption.tests.json_data import (
    test_redemption_lot_data,
)

DEFAULT_ACCELERATION = 1440


PARTIAL_MOCK_CONFIG = {
    "lots.redemption": {
        "use_default": True,
        "aliases": [],
        "accreditation": {
            "create": [1],
            "edit": [2]
        }
    }
}

if SANDBOX_MODE:
    test_redemption_lot_data['sandboxParameters'] = 'quick, accelerator={}'.format(DEFAULT_ACCELERATION)


def round_to_two_decimal_places(value):
    prec = Decimal('0.01')
    return float(Decimal(str(value)).quantize(prec, ROUND_HALF_UP).normalize())


MOCK_CONFIG = connection_mock_config(PARTIAL_MOCK_CONFIG,
                                     base=BASE_MOCK_CONFIG,
                                     connector=('plugins', 'api', 'plugins',
                                                'lots.core', 'plugins'))


class BaseLotWebTest(BaseLWT):
    initial_auth = ('Basic', ('broker', ''))
    relative_to = os.path.dirname(__file__)
    mock_config = MOCK_CONFIG

    def setUp(self):
        self.initial_data = deepcopy(test_redemption_lot_data)
        super(BaseLotWebTest, self).setUp()


class LotContentWebTest(BaseLotWebTest):
    init = True
    initial_status = 'pending'
    mock_config = MOCK_CONFIG
