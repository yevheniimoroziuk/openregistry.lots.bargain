# -*- coding: utf-8 -*-
from copy import deepcopy

from openregistry.lots.core.tests.base import create_blacklist

from openregistry.lots.bargain.models import Lot
from openregistry.lots.bargain.tests.json_data import (
    auction_common,
    test_loki_item_data
)
from openregistry.lots.bargain.constants import (
    STATUS_CHANGES,
    LOT_STATUSES,
    PLATFORM_LEGAL_DETAILS_DOC_DATA,
    DEFAULT_PROCUREMENT_TYPE
)
from openregistry.lots.bargain.tests.fixtures import (
    create_single_lot,
    check_patch_status_200,
    check_patch_status_403,
    add_decisions,
    add_auctions,
    add_lot_decision,
    add_lot_related_process,
    add_cancellationDetails_document,
    # status fixtures
    move_lot_to_composing,
    move_lot_to_verification,
    move_lot_to_pending,
    move_lot_to_active_auction,
    move_lot_to_active_contracting,
    move_lot_to_active_salable,
    move_lot_to_pending_sold,
    move_lot_to_sold,
    move_lot_to_deleted,
    move_lot_to_dissolved,
    move_lot_to_invalid,
    move_lot_to_pending_deleted,
    move_lot_to_pending_dissolution
)


ROLES = ['lot_owner', 'Administrator', 'concierge', 'convoy', 'chronograph']
STATUS_BLACKLIST = create_blacklist(STATUS_CHANGES, LOT_STATUSES, ROLES)


# LotTest
def simple_add_lot(self):
    u = Lot(self.initial_data)
    u.lotID = "UA-X"

    assert u.id is None
    assert u.rev is None

    u.store(self.db)

    assert u.id is not None
    assert u.rev is not None

    fromdb = self.db.get(u.id)

    assert u.lotID == fromdb['lotID']
    assert u.doc_type == "Lot"

    u.delete_instance(self.db)


def auction_autocreation(self):
    response = self.app.post_json('/', {"data": self.initial_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'draft')
    self.assertEqual(len(response.json['data']['auctions']), 1)
    auction = response.json['data']['auctions'][0]

    self.assertEqual(auction['procurementMethodType'], DEFAULT_PROCUREMENT_TYPE)
    self.assertEqual(auction['status'], 'scheduled')


def check_change_to_verification(self):
    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}/auctions'.format(lot['id']))
    auction = response.json['data'][0]

    auction_data = deepcopy(auction_common)

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft', access_header)

    # Move from 'draft' to 'composing' status
    move_lot_to_composing(self, lot, access_header)
    lot = add_lot_decision(self, lot['id'], access_header)

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    # Check if all required fields are filled in first english auction
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['name'],
        'auctions'
    )
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        {
            'value': ['This field is required.'],
            'bankAccount': ['This field is required.'],
        }
    )

    auction_data_without_bankAccount = deepcopy(auction_data)
    del auction_data_without_bankAccount['bankAccount']
    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction['id']),
        params={'data': auction_data_without_bankAccount}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        {
            'bankAccount': ['This field is required.']
        }
    )

    response = self.app.patch_json(
        '/{}/auctions/{}'.format(lot['id'], auction['id']),
        params={'data': auction_data}, headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    lot = add_lot_related_process(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Check when decisions not available
    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    add_auctions(self, lot, access_header)
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=403,
        headers=access_header
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t switch to verification while lot decisions not available.'
    )
    add_lot_decision(self, lot['id'], access_header)
    lot = add_lot_related_process(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': {'status': 'pending'}},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t switch to pending while decisions not available.'
    )
    add_decisions(self, lot)
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': {'status': 'pending'}},
        status=403
    )
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'Can\'t switch to pending while items in asset not available.'
    )

    # Check when relatedProcess not available
    self.app.authorization = ('Basic', ('broker', ''))

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_composing(self, lot, access_header)
    add_auctions(self, lot, access_header)
    add_lot_decision(self, lot['id'], access_header)
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        {"data": {'status': 'verification'}},
        status=422,
        headers=access_header
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(
        response.json['errors'][0]['description'],
        'You can set verification status '
        'only when lot have at least one relatedProcess'
    )
    lot = add_lot_related_process(self, lot['id'], access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)


def dateModified_resource(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json('/', {'data': self.initial_data})
    self.assertEqual(response.status, '201 Created')
    resource = response.json['data']

    token = str(response.json['access']['token'])
    dateModified = resource['dateModified']

    response = self.app.get('/{}'.format(resource['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['dateModified'], dateModified)

    response = self.app.patch_json(
        '/{}'.format(resource['id']),
        headers={'X-Access-Token': token},
        params={
            'data': {'status': 'composing'}
        }
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'composing')

    self.assertNotEqual(response.json['data']['dateModified'], dateModified)
    resource = response.json['data']
    dateModified = resource['dateModified']

    response = self.app.get('/{}'.format(resource['id']))

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], resource)
    self.assertEqual(response.json['data']['dateModified'], dateModified)


def simple_patch(self):
    data = deepcopy(self.initial_data)
    response = create_single_lot(self, data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(set(response.json['data']), set(lot))
    self.assertEqual(response.json['data'], lot)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    add_lot_decision(self, lot['id'], access_header)
    lot = add_lot_related_process(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})

    self.app.authorization = ('Basic', ('broker', ''))
    patch_data = {
        'data': {
            'officialRegistrationID': u'Інформація про державну реєстрацію'
        }
    }
    response = self.app.patch_json('/{}'.format(lot['id']), patch_data, headers=access_header)
    self.assertEqual(response.json['data']['officialRegistrationID'], patch_data['data']['officialRegistrationID'])


def change_draft_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft', access_header)

    # Move from 'draft' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)

    # Create lot in draft status
    draft_lot = deepcopy(draft_lot)
    draft_lot['status'] = 'draft'
    lot = create_single_lot(self, draft_lot).json['data']

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('convoy', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['convoy']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(draft_lot)
    draft_lot['status'] = 'draft'
    response = self.app.post_json('/', {'data': draft_lot}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')

    # Move from 'draft' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['draft']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move from 'draft' to 'draft' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'draft')

    # Move from 'draft' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')


def change_composing_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    move_lot_to_composing(self, lot, access_header)

    # Move from 'verification' to 'composing' status
    add_lot_decision(self, lot['id'], access_header)
    lot = add_lot_related_process(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    # Move from 'draft' to 'composing' status
    move_lot_to_composing(self, lot, access_header)

    # Move from 'composing' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['composing']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['composing']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['composing']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('broker', ''))
    add_lot_decision(self, lot['id'], access_header)
    lot = add_lot_related_process(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)

    self.app.authorization = ('Basic', ('administrator', ''))
    # Move from 'verification' to 'composing' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')

    # Create lot in 'draft' status
    self.app.authorization = ('Basic', ('broker', ''))
    draft_lot = deepcopy(self.initial_data)
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    # Move from 'draft' to 'composing' status
    move_lot_to_composing(self, lot, access_header)

    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['composing']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_verification_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    # Create lot in 'draft' status
    draft_lot = deepcopy(self.initial_data)
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    lot = move_lot_to_verification(self, lot, access_header)

    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['verification']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move from 'verification' to 'pending' status
    self.app.authorization = ('Basic', ('concierge', ''))
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})

    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_verification(self, lot, access_header)

    # Move from 'verification' to 'invalid' status
    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'invalid')

    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_verification(self, lot, access_header)

    # Move from 'verification' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['verification']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    # Move from 'verification' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['verification']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, draft_lot)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_verification(self, lot, access_header)

    # Move from 'verification' to 'composing' status
    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')


def change_pending_lot(self):

    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = deepcopy(self.initial_data)
    lot_info['status'] = 'draft'

    # Create lot in 'draft' status and move it to 'pending'
    response = create_single_lot(self, lot_info)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']), headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'pending' status
    move_lot_to_pending(self, lot, access_header)

    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', access_header)

    # Move status from Pending to Deleted 403
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   headers=access_header,
                                   params={'data': {'status': 'pending.deleted'}},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u"You can set deleted status "
        u"only when lot have at least one document with \'cancellationDetails\' documentType"
    )

    # Move from 'pending' to 'deleted' status
    add_cancellationDetails_document(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted', access_header)

    # Create lot in 'draft' status and move it to 'pending'
    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    move_lot_to_pending(self, lot, access_header)

    self.app.authorization = ('Basic', ('broker', ''))
    # Move from 'pending' to 'active.salable' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable', access_header)

    # Create lot in 'draft' status and move it to 'pending'
    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    move_lot_to_pending(self, lot, access_header)

    # Move from 'pending' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    # Move from 'pending' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending')

    # Move from 'pending' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['pending']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    # Move status from Pending to Deleted 403
    response = self.app.patch_json('/{}'.format(lot['id']),
                                   params={'data': {'status': 'pending.deleted'}},
                                   status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(
        response.json['errors'][0]['description'],
        u"You can set deleted status "
        u"only when lot have at least one document with \'cancellationDetails\' documentType"
    )

    # Move from 'pending' to 'deleted'
    self.app.authorization = ('Basic', ('broker', ''))
    add_cancellationDetails_document(self, lot, access_header)
    self.app.authorization = ('Basic', ('administrator', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.deleted')

    # Create lot in 'draft' status and move it to 'pending'
    self.app.authorization = ('Basic', ('broker', ''))
    response = create_single_lot(self, deepcopy(lot_info))
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    lot = response.json['data']

    move_lot_to_pending(self, lot, access_header)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'pending' to 'active.salable' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.salable', access_header)


def change_deleted_lot(self):

    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data
    lot_info['status'] = 'draft'

    # Create new lot in 'draft' status
    response = create_single_lot(self, lot_info)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}
    self.assertEqual(lot['status'], 'draft')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    move_lot_to_deleted(self, lot, access_header)

    self.app.authorization = ('Basic', ('broker', ''))
    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['deleted']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'deleted' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['deleted']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_active_salable_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.salable' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_salable(self, lot, access_header)

    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')

    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_salable(self, lot, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')

    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_salable(self, lot, access_header)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['active.salable']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'active.salable' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['active.salable']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.auction')

    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_salable(self, lot, access_header)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing')


def change_active_auction_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.auction' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_auction(self, lot, access_header)

    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['active.auction']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['active.auction']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['active.auction']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'active.contracting')

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_auction(self, lot, access_header)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.dissolution')

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_auction(self, lot, access_header)

    # Move from 'active.auction' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['active.auction']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_active_contracting_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'active.contracting' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_contracting(self, lot, access_header)

    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['active.contracting']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['active.contracting']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['active.contracting']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.sold')

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_contracting(self, lot, access_header)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending.dissolution')

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_active_contracting(self, lot, access_header)

    # Move from 'active.contracting' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['active.contracting']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_pending_sold_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'pending.sold' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_sold(self, lot, access_header)

    # Move from 'pending.sold' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending.sold']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'sold')

    # Create new lot in 'pending.sold' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_sold(self, lot, access_header)

    # Move from 'pending.sold' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending.sold']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending.sold']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'sold')


def change_pending_dissolution_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'pending.dissolution' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_dissolution(self, lot, access_header)

    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'dissolved')

    # Create new lot in 'pending.dissolution' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_dissolution(self, lot, access_header)

    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'dissolved')

    # Create new lot in 'pending.dissolution' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_dissolution(self, lot, access_header)

    # Move from 'pending.dissolution' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['pending.dissolution']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_sold_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'sold' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_sold(self, lot, access_header)

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['sold']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'sold' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['sold']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_dissolved_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'dissolved' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_dissolved(self, lot, access_header)

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['dissolved']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['dissolved']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['dissolved']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'dissolved' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['dissolved']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_invalid_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'invalid' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_invalid(self, lot, access_header)

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['invalid']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))

    # Move from 'invalid' to one of 'blacklist' status
    for status in STATUS_BLACKLIST['invalid']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def change_pending_deleted_lot(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    self.app.authorization = ('Basic', ('broker', ''))

    lot_info = self.initial_data

    # Create new lot in 'pending.deleted' status
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_deleted(self, lot, access_header)

    # Move from 'pending.deleted' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('broker', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['lot_owner']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status, access_header)

    self.app.authorization = ('Basic', ('concierge', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted')
    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['auctions'][0]['status'], 'cancelled')
    self.assertEqual(response.json['data']['contracts'][0]['status'], 'cancelled')

    # Create new lot in 'pending.deleted' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_deleted(self, lot, access_header)

    # Move from 'pending.deleted' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('concierge', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['concierge']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('chronograph', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['chronograph']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)

    self.app.authorization = ('Basic', ('administrator', ''))
    check_patch_status_200(self, '/{}'.format(lot['id']), 'deleted')
    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['auctions'][0]['status'], 'cancelled')
    self.assertEqual(response.json['data']['contracts'][0]['status'], 'cancelled')

    # Create new lot in 'pending.deleted' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    move_lot_to_pending_deleted(self, lot, access_header)

    # Move from 'pending.deleted' to one of 'blacklist' status
    self.app.authorization = ('Basic', ('administrator', ''))
    for status in STATUS_BLACKLIST['pending.deleted']['Administrator']:
        check_patch_status_403(self, '/{}'.format(lot['id']), status)


def check_auction_status_lot_workflow(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    lot_info = self.initial_data

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_active_auction(self, lot, access_header)

    auction = lot['auctions'][0]

    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], auction['id']),
                                   params={'data': {'status': 'unsuccessful'}})
    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.dissolution')
    contract = response.json['data']['contracts'][0]

    self.assertEqual(response.json['data']['auctions'][0]['status'], 'unsuccessful')
    self.assertEqual(contract['status'], 'cancelled')

    # Create new lot in 'active.auction' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_active_auction(self, lot, access_header)

    auction = lot['auctions'][0]

    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], auction['id']),
                                   params={'data': {'status': 'cancelled'}})
    self.assertEqual(response.json['data']['status'], 'cancelled')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.dissolution')
    auction = response.json['data']['auctions'][0]
    contract = response.json['data']['contracts'][0]

    self.assertEqual(auction['status'], 'cancelled')
    self.assertEqual(contract['status'], 'cancelled')

    # Create new lot in 'active.salable' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_active_salable(self, lot, access_header)

    auction = lot['auctions'][0]

    self.app.authorization = ('Basic', ('concierge', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], auction['id']),
                                   params={'data': {'status': 'active'}})
    self.assertEqual(response.json['data']['status'], 'active')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'active.auction')

    # Create new lot in 'active.auction' status and patch to complete
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_active_auction(self, lot, access_header)
    auction = lot['auctions'][0]

    self.app.authorization = ('Basic', ('convoy', ''))
    response = self.app.patch_json('/{}/auctions/{}'.format(lot['id'], auction['id']),
                                   params={'data': {'status': 'complete'}})
    self.assertEqual(response.json['data']['status'], 'complete')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'active.contracting')
    auction = response.json['data']['auctions'][0]

    self.assertEqual(auction['status'], 'complete')


def check_contract_status_workflow(self):
    response = self.app.get('/')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    lot_info = self.initial_data

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    contract_id = lot['contracts'][0]['id']

    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_active_contracting(self, lot, access_header)

    self.app.authorization = ('Basic', ('caravan', ''))
    response = self.app.patch_json('/{}/contracts/{}'.format(lot['id'], contract_id),
                                   params={'data': {'status': 'unsuccessful'}})

    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.dissolution')

    contract = response.json['data']['contracts'][0]
    self.assertEqual(contract['status'], 'unsuccessful')

    # Create new lot in 'active.contracting' status
    self.app.authorization = ('Basic', ('broker', ''))
    json = create_single_lot(self, lot_info).json
    lot = json['data']
    contract_id = lot['contracts'][0]['id']
    token = json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot = move_lot_to_active_contracting(self, lot, access_header)

    self.app.authorization = ('Basic', ('caravan', ''))
    response = self.app.patch_json('/{}/contracts/{}'.format(lot['id'], contract_id),
                                   params={'data': {'status': 'complete'}})

    self.assertEqual(response.json['data']['status'], 'complete')

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.json['data']['status'], 'pending.sold')

    contract = response.json['data']['contracts'][0]
    self.assertEqual(contract['status'], 'complete')


def adding_platformLegalDetails_doc(self):
    response = self.app.post_json('/', {'data': self.initial_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(len(response.json['data']['documents']), 1)
    document = response.json['data']['documents'][0]
    self.assertEqual(document['title'], PLATFORM_LEGAL_DETAILS_DOC_DATA['title'])
    self.assertEqual(document['url'], PLATFORM_LEGAL_DETAILS_DOC_DATA['url'])
    self.assertEqual(document['documentOf'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentOf'])
    self.assertEqual(document['documentType'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentType'])
    self.assertIsNotNone(document.get('id'))

    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    lot_id = response.json['data']['id']
    doc_id = document['id']

    response = self.app.get('/{}/documents/{}'.format(lot_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['title'], PLATFORM_LEGAL_DETAILS_DOC_DATA['title'])
    self.assertEqual(response.json['data']['description'], PLATFORM_LEGAL_DETAILS_DOC_DATA['description'])
    self.assertEqual(response.json['data']['url'], PLATFORM_LEGAL_DETAILS_DOC_DATA['url'])
    self.assertEqual(response.json['data']['documentOf'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentOf'])
    self.assertEqual(response.json['data']['documentType'], PLATFORM_LEGAL_DETAILS_DOC_DATA['documentType'])

    check_patch_status_200(self, '/{}'.format(lot_id), 'composing', access_header)

    response = self.app.patch_json(
        '/{}/documents/{}'.format(lot_id, doc_id),
        params={'data': {'title': 'another'}},
        headers=access_header
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['title'], 'another')
