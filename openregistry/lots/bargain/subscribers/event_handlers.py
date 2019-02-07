# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from openregistry.lots.core.events import LotInitializeEvent
from openprocurement.api.utils import get_now


@subscriber(LotInitializeEvent, _internal_type="bargain")
def lot_init_handler(event):
    """ initialization handler for basic lots """
    event.lot.date = get_now()
