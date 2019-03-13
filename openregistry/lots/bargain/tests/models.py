# -*- coding: utf-8 -*-
import unittest

from schematics.exceptions import ModelValidationError

from openregistry.lots.core.utils import get_now

from openregistry.lots.bargain.constants import DEFAULT_PROCUREMENT_TYPE
from openregistry.lots.bargain.models import (
    BankAccount,
    Auction,
    Lot
)

now = get_now()


class DummyModelsTest(unittest.TestCase):

    def test_BankAccount(self):
        data = {
            'name': 'Name'
        }

        account_details = BankAccount()
        self.assertEqual(account_details.serialize(), None)
        with self.assertRaisesRegexp(ValueError, 'BankAccount Model has no role "test"'):
            account_details.serialize('test')

        account_details.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            account_details.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'accountIdentification': [u'Please provide at least 1 item.'],
                'bankName': [u'This field is required.']
            }
        )

        data['accountIdentification'] = [
            {
                'scheme': 'wrong',
                'id': '1231232'
            }
        ]
        data['bankName'] = 'bankName'
        account_details.import_data(data)
        with self.assertRaises(ModelValidationError) as ex:
            account_details.validate()
        self.assertEqual(
            ex.exception.messages,
            {
                'accountIdentification':
                [
                    {
                     'scheme': [u"Value must be one of ['UA-EDR', 'UA-MFO', 'accountNumber']."],
                     'description': [u"This field is required."]
                    }
                ]
            }
        )

        data['accountIdentification'] = [
            {
                'scheme': 'UA-MFO',
                'id': '1231232',
                'description': 'just description'
            }
        ]
        account_details.import_data(data)
        account_details.validate()

    def test_Auction(self):
        data = {
            "procurementMethodType": DEFAULT_PROCUREMENT_TYPE,
            "guarantee": {
                "amount": 30.54,
                "currency": "UAH"
            },
            "value": {
                "amount": 1500.54,
                "currency": "UAH"
            },
        }
        lot = Lot()
        lot.status = 'draft'
        data['__parent__'] = lot
        auction = Auction()
        auction.import_data(data)
        auction.validate()

        auction.import_data(data)

        data['relatedProcessID'] = 'relatedProcessID'
        data['auctionID'] = 'auctionID'

        auction.import_data(data)

        edit_serialization = auction.serialize('edit')
        self.assertNotIn('relatedProcessID', edit_serialization)
        self.assertNotIn('auctionID', edit_serialization)

        edit_serialization = auction.serialize('create')
        self.assertNotIn('relatedProcessID', edit_serialization)
        self.assertNotIn('auctionID', edit_serialization)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(DummyModelsTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
