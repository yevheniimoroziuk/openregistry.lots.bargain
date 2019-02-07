# -*- coding: utf-8 -*-
import unittest

from copy import deepcopy

from openregistry.lots.core.constants import SANDBOX_MODE


from openregistry.lots.bargain.constants import DEFAULT_PROCUREMENT_TYPE
from openregistry.lots.bargain.tests.json_data import test_loki_item_data
from openregistry.lots.bargain.tests.fixtures import (
    create_single_lot,
    check_patch_status_200,
    add_decisions,
    add_auctions,
    add_lot_decision,
    add_lot_related_process,
    move_lot_to_pending
)


def patch_auctions_with_lot(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    move_lot_to_pending(self, lot, self.access_header)

    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    # Move from 'draft' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    lot = add_lot_decision(self, lot['id'], access_header)
    add_lot_related_process(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


    self.app.authorization = ('Basic', ('concierge', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})


def patch_auction_by_concierge(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    move_lot_to_pending(self, lot, self.access_header)

    data = deepcopy(self.initial_auction_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auction = response.json['data'][0]
    data['value']['amount'] = 99

    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, auction['id']),
        headers=self.access_header, params={
            'data': data
            })

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['id'], auction['id'])
    self.assertEqual(response.json['data']['value'], data['value'])
    self.assertEqual(response.json['data']['guarantee'], data['guarantee'])

    self.app.authorization = ('Basic', ('concierge', ''))
    
    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, auction['id']),
        headers=self.access_header, params={
            'data': {
                'status': 'unsuccessful',
                'auctionID': 'someAuctionID',
                'relatedProcessID': '1' * 32
            }
            })
    self.assertEqual(response.json['data']['status'], 'unsuccessful')
    self.assertEqual(response.json['data']['auctionID'], 'someAuctionID')
    self.assertEqual(response.json['data']['relatedProcessID'], '1' * 32)


def patch_auction(self):
    self.set_status('composing')

    data = deepcopy(self.initial_auction_data)
    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auction = response.json['data'][0]

    response = self.app.patch_json('/{}/auctions/{}'.format(self.resource_id, auction['id']),
        headers=self.access_header, params={
            'data': data
            })

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['id'], auction['id'])
    self.assertEqual(response.json['data']['value'], data['value'])
    self.assertEqual(response.json['data']['guarantee'], data['guarantee'])

    response = self.app.get('/{}/auctions'.format(self.resource_id))
    auction = response.json['data'][0]

    self.assertEqual(auction['procurementMethodType'], DEFAULT_PROCUREMENT_TYPE)
    self.assertEqual(auction['value']['amount'], data['value']['amount'])
    self.assertEqual(auction['guarantee']['amount'], data['guarantee']['amount'])


@unittest.skipIf(not SANDBOX_MODE, 'If sandbox mode is enabled auctionParameters has additional field procurementMethodDetails')
def procurementMethodDetails_check_with_sandbox(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    move_lot_to_pending(self, lot, self.access_header)

    # Test procurementMethodDetails after creating lot
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    auction = response.json['data']['auctions'][0]

    self.assertNotIn(
        'procurementMethodDetails',
        auction
    )

    auction_param_with_procurementMethodDetails = {'procurementMethodDetails': 'quick'}

    # Test procurementMethodDetails after update lot auction
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header
    )
    self.assertEqual(
        response.json['data']['procurementMethodDetails'],
        auction_param_with_procurementMethodDetails['procurementMethodDetails']
    )


@unittest.skipIf(SANDBOX_MODE, 'If sandbox mode is disabled auctionParameters has not procurementMethodDetails field')
def procurementMethodDetails_check_without_sandbox(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']
    move_lot_to_pending(self, lot, self.access_header)

    auction = response.json['data']['auctions'][0]

    self.assertNotIn(
        'procurementMethodDetails',
        response.json['data']['auctions'][0],
    )

    auction_param_with_procurementMethodDetails = {'procurementMethodDetails': 'quick'}

    # Test procurementMethodDetails error while updating lot auction
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction['id']),
        {'data': auction_param_with_procurementMethodDetails},
        headers=self.access_header,
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]['description'], u'Rogue field')
    self.assertEqual(response.json['errors'][0]['name'], 'procurementMethodDetails')
