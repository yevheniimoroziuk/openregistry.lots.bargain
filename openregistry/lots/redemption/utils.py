# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    context_unpack,
    LOGGER
)


def process_convoy_auction_report_result(request):
    lot = request.validated['lot']

    is_lot_need_to_be_dissolved = bool(request.validated['auction'].status in ['cancelled', 'unsuccessful'])

    if lot.status == 'active.auction' and is_lot_need_to_be_dissolved:
        LOGGER.info('Switched lot %s to %s', lot.id, 'pending.dissolution',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_pending.dissolution'}))

        lot.status = 'pending.dissolution'
        lot.contracts[0].status = 'cancelled'

    elif lot.status == 'active.auction' and request.validated['auction'].status == 'complete':
        LOGGER.info('Switched lot %s to %s', lot.id, 'active.contracting',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_active.contracting'}))
        lot.status = 'active.contracting'


def process_concierge_auction_status_change(request):
    lot = request.validated['lot']

    if lot.status == 'active.salable' and request.validated['auction'].status == 'active':
        LOGGER.info('Switched lot %s to %s', lot.id, 'active.auction',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_active.auction'}))
        lot.status = 'active.auction'


def process_lot_status_change(request):
    lot = request.context

    if lot.status == 'pending.deleted' and request.validated['data'].get('status') == 'deleted':
        for auction in lot.auctions:
            auction.status = 'cancelled'
        lot.contracts[0].status = 'cancelled'


def process_caravan_contract_report_result(request):
    lot = request.validated['lot']
    contract = request.validated['contract']

    if lot.status == 'active.contracting' and contract.status == 'unsuccessful':
        LOGGER.info('Switched lot %s to %s', lot.id, 'pending.dissolution',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_pending.dissolution'}))
        lot.status = 'pending.dissolution'
    elif lot.status == 'active.contracting' and contract.status == 'complete':
        LOGGER.info('Switched lot %s to %s', lot.id, 'pending.sold',
                    extra=context_unpack(request, {'MESSAGE_ID': 'switched_lot_pending.sold'}))
        lot.status = 'pending.sold'
