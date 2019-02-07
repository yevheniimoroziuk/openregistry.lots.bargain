# -*- coding: utf-8 -*-
from copy import deepcopy

from openregistry.lots.core.utils import get_now

from openregistry.lots.core.tests.blanks.json_data import (
    test_document_data,
    test_item_data,
)


now = get_now()
test_bargain_document_data = deepcopy(test_document_data)
test_bargain_document_data['documentType'] = 'notice'
test_bargain_document_data['documentOf'] = 'lot'

auction_common = {
    'value': {
        'amount': 3000.87,
        'currency': 'UAH',
        'valueAddedTaxIncluded': True
    },
    'guarantee': {
        'amount': 700.87,
        'currency': 'UAH'
    },
    'bankAccount': {
        'bankName': 'name of bank',
        'accountIdentification': [
            {
                'scheme': 'accountNumber',
                'id': '111111-8',
                'description': 'some description'
            }
        ]
    }
}


test_bargain_lot_data = {
    "title": u"Тестовий лот",
    "description": u"Щось там тестове",
    "lotType": "bargain"
}
test_decision_data = {
    'decisionID': 'someDecisionID',
    'decisionDate': get_now().isoformat()
}

test_loki_item_data = deepcopy(test_item_data)
test_loki_item_data['registrationDetails'] = {
    'status': 'unknown'
}
test_loki_item_data.update(
    {
        "unit": {"code": "code"},
        "classification": {
            "scheme": "CPV",
            "id": "73110000-6",
            "description": "Description"
        },
        "address": {"countryName": "Ukraine"},
        "quantity": 5.0001,
        "additionalClassifications": [
            {
                "scheme": u"UA-EDR",
                "id": u"111111-4",
                "description": u"папір і картон гофровані, паперова й картонна тара"
            }
        ]
    }
)

test_lot_contract_data = {
    'contractID': 'contractID',
    'relatedProcessID': '1' * 32
}

test_related_process_data = {
    'relatedProcessID': '1' * 32,
    'type': 'asset'
}
