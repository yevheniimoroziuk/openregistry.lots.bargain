# -*- coding: utf-8 -*-
from openregistry.lots.core.adapters import (
    LotConfigurator,
    LotManagerAdapter,
    Manager,
)
from openregistry.lots.core.validation import (
    validate_post_lot_role,

)
from openregistry.lots.core.utils import (
    get_now,
    apply_patch,
    save_lot,
    validate_with,
)
from openregistry.lots.bargain.utils import (
    process_lot_status_change
)
from openregistry.lots.bargain.constants import (
    STATUS_CHANGES,
    ITEM_EDITING_STATUSES,
    DECISION_EDITING_STATUSES,
    CONTRACT_TYPE,
    PLATFORM_LEGAL_DETAILS_DOC_DATA,
    DEFAULT_PROCUREMENT_TYPE
)
from openregistry.lots.bargain.validation import (
    validate_pending_status,
    validate_deleted_status,
    validate_verification_status,
    validate_related_process_operation_in_not_allowed_lot_status
)


class BargainLotConfigurator(LotConfigurator):
    """ Bargain Tender configuration adapter """

    name = "Bargain Lot configurator"
    available_statuses = STATUS_CHANGES
    item_editing_allowed_statuses = ITEM_EDITING_STATUSES
    decision_editing_allowed_statuses = DECISION_EDITING_STATUSES


class RelatedProcessManager(Manager):
    create_validators = (
        validate_related_process_operation_in_not_allowed_lot_status,
    )
    update_validators = (
        validate_related_process_operation_in_not_allowed_lot_status,
    )
    delete_validators = (
        validate_related_process_operation_in_not_allowed_lot_status,
    )

    @validate_with(create_validators)
    def create(self, request):
        self.lot.relatedProcesses.append(request.validated['relatedProcess'])
        return save_lot(request)

    @validate_with(update_validators)
    def update(self, request):
        return apply_patch(request, src=request.context.serialize())

    @validate_with(delete_validators)
    def delete(self, request):
        self.lot.relatedProcesses.remove(request.validated['relatedProcess'])
        self.lot.modified = False
        return save_lot(request)


class BargainLotManagerAdapter(LotManagerAdapter):
    name = 'Bargain Lot Manager'
    create_validation = (
        validate_post_lot_role,
    )
    change_validation = (
        validate_pending_status,
        validate_deleted_status,
        validate_verification_status,
    )

    def __init__(self, *args, **kwargs):
        super(BargainLotManagerAdapter, self).__init__(*args, **kwargs)
        self.related_processes_manager = RelatedProcessManager(
            parent=self.context,
            parent_name='lot'
        )

    def _create_auctions(self, request):
        lot = request.validated['lot']
        lot.date = get_now()
        auction_types = [DEFAULT_PROCUREMENT_TYPE]
        auction_class = lot.__class__.auctions.model_class

        for auction_type in auction_types:
            data = dict()
            data['procurementMethodType'] = auction_type
            data['status'] = 'scheduled'

            data['__parent__'] = lot
            lot.auctions.append(auction_class(data))

    def _create_contracts(self, request):
        lot = request.validated['lot']
        contract_class = lot.__class__.contracts.model_class
        lot.contracts.append(contract_class({'type': CONTRACT_TYPE}))

    def _add_x_PlatformLegalDetails_document(self, request):
        lot = request.validated['lot']
        document_class = lot.__class__.documents.model_class
        document = document_class(PLATFORM_LEGAL_DETAILS_DOC_DATA)
        lot.documents.append(document)

    def create_lot(self, request):
        self._validate(request, self.create_validation)
        self._create_auctions(request)
        self._create_contracts(request)
        self._add_x_PlatformLegalDetails_document(request)

    def change_lot(self, request):
        self._validate(request, self.change_validation)

        if request.authenticated_role in ('concierge', 'Administrator'):
            process_lot_status_change(request)
            request.validated['lot_src'] = self.context.serialize('plain')
