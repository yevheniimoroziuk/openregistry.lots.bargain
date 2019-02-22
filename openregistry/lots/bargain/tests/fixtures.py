# -*- coding: utf-8 -*-
from copy import deepcopy
from uuid import uuid4

from openregistry.lots.core.utils import get_now
from openregistry.lots.bargain.tests.json_data import (
    auction_common,
    test_loki_item_data
)


def add_cancellationDetails_document(self, lot, access_header):
    # Add cancellationDetails document
    test_document_data = {
        'title': u'укр.doc',
        'hash': 'md5:' + '0' * 32,
        'format': 'application/msword',
        'documentType': 'cancellationDetails'
    }
    test_document_data['url'] = self.generate_docservice_url()

    response = self.app.post_json('/{}/documents'.format(lot['id']),
                                  headers=access_header,
                                  params={'data': test_document_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    tender = self.db.get(lot['id'])
    self.assertIn(key, tender['documents'][-1]["url"])
    self.assertIn('Signature=', tender['documents'][-1]["url"])
    self.assertIn('KeyID=', tender['documents'][-1]["url"])
    self.assertNotIn('Expires=', tender['documents'][-1]["url"])


def add_decisions(self, lot):
    asset_decision = {
            'decisionDate': get_now().isoformat(),
            'decisionID': 'decisionAssetID',
            'decisionOf': 'asset',
            'relatedItem': '1' * 32
        }
    data_with_decisions = {
        "decisions": [
            lot['decisions'][0], asset_decision
        ]
    }
    response = self.app.patch_json('/{}'.format(lot['id']), params={'data': data_with_decisions})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['decisions'][0]['decisionOf'], 'lot')
    self.assertEqual(response.json['data']['decisions'][0]['id'], data_with_decisions['decisions'][0]['id'])
    self.assertEqual(
        response.json['data']['decisions'][0]['decisionID'],
        data_with_decisions['decisions'][0]['decisionID']
    )
    self.assertNotIn('relatedItem', response.json['data']['decisions'][0])

    self.assertEqual(response.json['data']['decisions'][1]['decisionOf'], 'asset')
    self.assertIsNotNone(response.json['data']['decisions'][1].get('id'))
    self.assertEqual(
        response.json['data']['decisions'][1]['decisionID'],
        data_with_decisions['decisions'][1]['decisionID']
    )
    self.assertEqual(
        response.json['data']['decisions'][1]['relatedItem'],
        data_with_decisions['decisions'][1]['relatedItem']
    )


def add_auctions(self, lot, access_header):
    response = self.app.get('/{}/auctions'.format(lot['id']))
    english = response.json['data'][0]

    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], english['id']),
        params={'data': auction_common}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')


def check_patch_status_200(self, path, lot_status, headers=None, extra={}):
    data = {'status': lot_status}
    data.update(extra)
    response = self.app.patch_json(path,
                                   headers=headers,
                                   params={'data': data})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], lot_status)


def check_patch_status_403(self, path, lot_status, headers=None):

    # Check if response.status is forbidden, when you try to change status to incorrect
    # 'data' should be {'data': {'status': allowed_status}}
    response = self.app.patch_json(path,
                                   params={'data': {'status': lot_status}},
                                   headers=headers,
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')


def create_single_lot(self, data, status=None):
    response = self.app.post_json('/', {"data": data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'draft')
    self.assertNotIn('decisions', response.json['data'])
    self.assertEqual(len(response.json['data']['auctions']), 1)
    token = response.json['access']['token']
    lot_id = response.json['data']['id']

    if status:
        access_header = {'X-Access-Token': str(token)}
        add_auctions(self, response.json['data'], access_header)
        fromdb = self.db.get(lot_id)
        fromdb = self.lot_model(fromdb)

        fromdb.status = status
        fromdb.store(self.db)

        response = self.app.get('/{}'.format(lot_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['id'], lot_id)
        self.assertEqual(response.json['data']['status'], status)
        new_json = deepcopy(response.json)
        new_json['access'] = {'token': token}
        return new_json

    return response


def add_lot_decision(self, lot_id, headers):
    old_authorization = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.get('/{}'.format(lot_id))
    old_decs_count = len(response.json['data'].get('decisions', []))

    decision_data = {
        'decisionDate': get_now().isoformat(),
        'decisionID': 'decisionLotID'
    }
    response = self.app.post_json(
        '/{}/decisions'.format(lot_id),
        {"data": decision_data},
        headers=headers
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.json['data']['decisionDate'], decision_data['decisionDate'])
    self.assertEqual(response.json['data']['decisionID'], decision_data['decisionID'])

    response = self.app.get('/{}'.format(lot_id))
    present_decs_count = len(response.json['data'].get('decisions', []))
    self.assertEqual(old_decs_count + 1, present_decs_count)

    self.app.authorization = old_authorization
    return response.json['data']


def add_lot_related_process(self, lot_id, headers):
    old_authorization = self.app.authorization
    self.app.authorization = ('Basic', ('broker', ''))

    response = self.app.get('/{}'.format(lot_id))
    old_related_processes = len(response.json['data'].get('relatedProcesses', []))

    rP_data = {
        'relatedProcessID': uuid4().hex,
    }
    response = self.app.post_json(
        '/{}/related_processes'.format(lot_id),
        {"data": rP_data},
        headers=headers
    )
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.json['data']['relatedProcessID'], rP_data['relatedProcessID'])

    response = self.app.get('/{}'.format(lot_id))
    present_related_processes = len(response.json['data'].get('relatedProcesses', []))
    self.assertEqual(old_related_processes + 1, present_related_processes)

    self.app.authorization = old_authorization
    return response.json['data']


def idempotent_auth(func):

    def func_wrapper(test_case, lot, access_header):
        old_auth = test_case.app.authorization
        result = func(test_case, lot, access_header)
        test_case.app.authorization = old_auth
        return result

    return func_wrapper


@idempotent_auth
def move_lot_to_composing(test_case, lot, access_header):
    test_case.app.authorization = ('Basic', ('broker', ''))
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'composing', access_header)

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_verification(test_case, lot, access_header):
    lot = move_lot_to_composing(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('broker', ''))
    add_lot_decision(test_case, lot['id'], access_header)
    add_lot_related_process(test_case, lot['id'], access_header)
    add_auctions(test_case, lot, access_header)

    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'verification', access_header)

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_pending(test_case, lot, access_header):
    lot = move_lot_to_verification(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(test_case, lot)
    check_patch_status_200(
        test_case,
        '/{}'.format(lot['id']),
        'pending',
        extra={'items': [test_loki_item_data]}
    )

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_active_salable(test_case, lot, access_header):
    lot = move_lot_to_pending(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('broker', ''))
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'active.salable', access_header)

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_active_auction(test_case, lot, access_header):
    lot = move_lot_to_active_salable(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('concierge', ''))

    auction_id = lot['auctions'][0]['id']
    test_case.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction_id),
        params={'data': {'status': 'active'}}
    )

    response = test_case.app.get('/{}'.format(lot['id']), status=200)
    test_case.assertEqual(response.json['data']['status'], 'active.auction')

    return response.json['data']


@idempotent_auth
def move_lot_to_active_contracting(test_case, lot, access_header):
    lot = move_lot_to_active_auction(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('convoy', ''))

    auction_id = lot['auctions'][0]['id']
    test_case.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction_id),
        params={'data': {'status': 'complete'}}
    )

    response = test_case.app.get('/{}'.format(lot['id']), status=200)
    test_case.assertEqual(response.json['data']['status'], 'active.contracting')

    return response.json['data']


@idempotent_auth
def move_lot_to_pending_sold(test_case, lot, access_header):
    lot = move_lot_to_active_contracting(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('caravan', ''))

    contract_id = lot['contracts'][0]['id']
    test_case.app.patch_json(
        '/{}/contracts/{}'.format(lot['id'], contract_id),
        params={'data': {'status': 'complete'}}
    )

    response = test_case.app.get('/{}'.format(lot['id']), status=200)
    test_case.assertEqual(response.json['data']['status'], 'pending.sold')

    return response.json['data']


@idempotent_auth
def move_lot_to_sold(test_case, lot, access_header):
    lot = move_lot_to_pending_sold(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'sold')

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_pending_deleted(test_case, lot, access_header):
    lot = move_lot_to_pending(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('broker', ''))
    add_cancellationDetails_document(test_case, lot, access_header)
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'pending.deleted', access_header)

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_deleted(test_case, lot, access_header):
    lot = move_lot_to_pending_deleted(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'deleted')

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_invalid(test_case, lot, access_header):
    lot = move_lot_to_verification(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'invalid')

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']


@idempotent_auth
def move_lot_to_pending_dissolution(test_case, lot, access_header):
    lot = move_lot_to_active_auction(test_case, lot, access_header)
    test_case.app.authorization = ('Basic', ('convoy', ''))
    auction_id = lot['auctions'][0]['id']
    test_case.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction_id),
        params={'data': {'status': 'unsuccessful'}}
    )

    response = test_case.app.get('/{}'.format(lot['id']), status=200)
    test_case.assertEqual(response.json['data']['status'], 'pending.dissolution')

    return response.json['data']


@idempotent_auth
def move_lot_to_dissolved(test_case, lot, access_header):
    lot = move_lot_to_pending_dissolution(test_case, lot, access_header)

    test_case.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(test_case, '/{}'.format(lot['id']), 'dissolved')

    return test_case.app.get('/{}'.format(lot['id']), status=200).json['data']
