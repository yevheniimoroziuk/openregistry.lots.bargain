# -*- coding: utf-8 -*-
from copy import copy
from openregistry.lots.core.constants import LOKI_DOCUMENT_TYPES


AUCTION_STATUSES = ['scheduled', 'active', 'complete', 'unsuccessful', 'cancelled']
CONTRACT_STATUSES = ['scheduled', 'cancelled', 'active', 'unsuccessful', 'complete']

CONTRACT_TYPE = 'yoke'

LOT_STATUSES = [
    "draft", "composing", "verification", "pending", "pending.deleted", "deleted", "active.salable",
    "active.auction", "active.contracting", "pending.sold", "pending.dissolution", "sold", "dissolved", "invalid"]

ITEM_EDITING_STATUSES = ['pending']

STATUS_CHANGES = {
    "draft": {
        "editing_permissions": ["lot_owner", "Administrator"],
        "next_status": {
            "composing": ["lot_owner", "Administrator"],
        }
    },
    "composing": {
        "editing_permissions": ["lot_owner", "Administrator"],
        "next_status": {
            "verification": ["lot_owner", "Administrator"]
        }
    },
    "verification": {
        "editing_permissions": ["concierge"],
        "next_status": {
            "composing": ["concierge"],
            "pending": ["concierge"],
            "invalid": ["concierge"],
        }
    },
    "pending": {
        "editing_permissions": ["lot_owner", "Administrator", "chronograph"],
        "next_status": {
            "pending.deleted": ["lot_owner", "Administrator"],
            "active.salable": ["lot_owner", "Administrator"],
        }
    },
    "pending.deleted": {
        "editing_permissions": ["concierge", "Administrator"],
        "next_status": {
            "deleted": ["concierge", "Administrator"],
        }
    },
    "deleted": {
        "editing_permissions": [],
        "next_status": {}
    },
    "active.salable": {
        "editing_permissions": ["Administrator", "concierge"],
        "next_status": {
            "active.auction": ["Administrator", "concierge"],
            "composing": ["Administrator", "concierge"],
        }
    },
    "active.auction": {
        "editing_permissions": ["Administrator"],
        "next_status": {
            "active.contracting": ["Administrator"],
            "pending.dissolution": ["Administrator"],
        }
    },
    "active.contracting": {
        "editing_permissions": ["Administrator", "caravan"],
        "next_status": {
            "pending.sold": ["Administrator"],
            "pending.dissolution": ["Administrator"],
        }
    },
    "pending.sold": {
        "editing_permissions": ["Administrator", "concierge"],
        "next_status": {
            "sold": ["Administrator", "concierge"]
        }
    },
    "pending.dissolution": {
        "editing_permissions": ["Administrator", "concierge"],
        "next_status": {
            "dissolved": ["Administrator", "concierge"]
        }
    },
    "sold": {
        "editing_permissions": [],
        "next_status": {}
    },
    "dissolved": {
        "editing_permissions": [],
        "next_status": {}
    },
    "invalid": {
        "editing_permissions": [],
        "next_status": {}
    },
}


LOT_DOCUMENT_TYPES = copy(LOKI_DOCUMENT_TYPES)
LOT_DOCUMENT_TYPES.extend(
    ['x_PlatformLegalDetails']
)

PLATFORM_LEGAL_DETAILS_DOC_DATA = {
    'title': u'Перелік та реквізити авторизованих електронних майданчиків',
    'description': u'Перелік та реквізити авторизованих електронних майданчиків '
                   u'(найменування установи банку, її адреса та номери рахунків, '
                   u'відкритих для внесення гарантійного внеску, реєстраційного внеску)',
    'url': 'https://prozorro.sale/info/elektronni-majdanchiki-ets-prozorroprodazhi-cbd2',
    'documentOf': 'lot',
    'documentType': 'x_PlatformLegalDetails',
}


DEFAULT_LOT_TYPE = 'bargain'

DECISION_EDITING_STATUSES = ['pending', 'composing']
CURRENCY_CHOICES = ['UAH']
DEFAULT_LEVEL_OF_ACCREDITATION = {'create': [1],
                                  'edit': [2]}

DEFAULT_PROCUREMENT_TYPE = 'reporting'
