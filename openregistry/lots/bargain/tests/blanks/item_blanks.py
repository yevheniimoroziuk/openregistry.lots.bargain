# -*- coding: utf-8 -*-
from copy import deepcopy
from uuid import uuid4

from openregistry.lots.bargain.tests.json_data import test_loki_item_data
from openregistry.lots.bargain.tests.fixtures import (
    add_decisions,
    add_lot_decision,
    add_auctions,
    check_patch_status_200,
    create_single_lot,
    add_lot_related_process
)


def item_listing(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')

    response = self.app.get('/{}/items'.format(self.resource_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']), len(self.initial_data['items']))

    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])

    response = self.app.get('/{}/items'.format(self.resource_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']), len(self.initial_data['items']) + 1)


def update_items_in_forbidden(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')

    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])

    data = self.initial_item_data
    data['quantity'] = 99.9999
    for status in self.forbidden_item_statuses_modification:
        self.set_status(status)
        response = self.app.patch_json(
            '/{}/items/{}'.format(self.resource_id, item_id),
            headers=self.access_header,
            params={"data": data},
            status=403
        )
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update item in current ({}) {} status".format(status, self.resource_name[:-1]))

    for status in self.forbidden_item_statuses_modification:
        self.set_status(status)
        response = self.app.post_json(
            '/{}/items'.format(self.resource_id),
            headers=self.access_header,
            params={"data": self.initial_item_data},
            status=403
        )
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update item in current ({}) {} status".format(status, self.resource_name[:-1]))


def create_item_resource(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')

    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')

    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])


def patch_item(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')

    response = self.app.post_json('/{}/items'.format(self.resource_id),
                                  headers=self.access_header,
                                  params={'data': self.initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])

    response = self.app.patch_json(
        '/{}/items/{}'.format(self.resource_id, item_id),
        headers=self.access_header,
        params={
            "data": {
                "description": "new item description",
                "registrationDetails": self.initial_item_data['registrationDetails'],
                "unit": self.initial_item_data['unit'],
                "address": self.initial_item_data['address'],
                "quantity": self.initial_item_data['quantity'],
                "classification": self.initial_item_data['classification'],
            }
        }
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(item_id, response.json["data"]["id"])
    self.assertEqual(response.json["data"]["description"], 'new item description')

    # Test partial update
    response = self.app.patch_json(
        '/{}/items/{}'.format(self.resource_id, item_id),
        headers=self.access_header,
        params={
            "data": {
                "description": "partial item update",
                "additionalClassifications": []
            }
        }
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(item_id, response.json["data"]["id"])
    self.assertEqual(response.json["data"]["description"], 'partial item update')
    self.assertNotIn('additionalClassifications', response.json['data'])


def patch_items_with_lot(self):
    response = self.app.get('/{}'.format(self.resource_id))
    lot = response.json['data']

    self.set_status('draft')
    add_auctions(self, lot, access_header=self.access_header)
    self.set_status('pending')

    # Create lot in 'draft' status and move it to 'pending'
    initial_item_data = deepcopy(self.initial_item_data)
    del initial_item_data['id']

    response = create_single_lot(self, self.initial_data)
    lot = response.json['data']
    token = response.json['access']['token']
    access_header = {'X-Access-Token': str(token)}

    response = self.app.get('/{}'.format(lot['id']), headers=access_header)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    # Move from 'draft' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'composing', access_header)
    add_lot_decision(self, lot['id'], access_header)
    lot = add_lot_related_process(self, lot['id'], access_header)
    add_auctions(self, lot, access_header)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification', access_header)

    self.app.authorization = ('Basic', ('concierge', ''))

    check_patch_status_200(self, '/{}'.format(lot['id']), 'verification')
    add_decisions(self, lot)
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', extra={'items': [test_loki_item_data]})

    self.app.authorization = ('Basic', ('broker', ''))

    # Move from 'pending' to 'pending' status
    check_patch_status_200(self, '/{}'.format(lot['id']), 'pending', access_header)

    response = self.app.post_json('/{}/items'.format(lot['id']),
                                  headers=access_header,
                                  params={'data': initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])

    response = self.app.post_json('/{}/items'.format(lot['id']),
                                  headers=access_header,
                                  params={'data': initial_item_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    item_id = response.json["data"]['id']
    self.assertIn(item_id, response.headers['Location'])
    self.assertEqual(self.initial_item_data['description'], response.json["data"]["description"])
    self.assertEqual(self.initial_item_data['quantity'], response.json["data"]["quantity"])
    self.assertEqual(self.initial_item_data['address'], response.json["data"]["address"])

    response = self.app.get('/{}'.format(lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']['items']), 3)

    data = {
        'items': [initial_item_data]
    }
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': data}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']['items']), 1)

    item_data = deepcopy(self.initial_item_data)
    item_data['id'] = uuid4().hex
    data = {
        'items': [item_data, item_data]
    }
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': data},
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(
        response.json['errors'][0]['description'][0],
        u'Item id should be uniq for all items'
    )

    data = {
        'items': [item_data]
    }
    response = self.app.patch_json(
        '/{}'.format(lot['id']),
        headers=access_header,
        params={'data': data}
    )
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(
        response.json['data']['id'],
        item_data['id']
    )


def create_item_resource_invalid(self):
    pass


def patch_item_resource_invalid(self):
    pass


def list_item_resource(self):
    pass
