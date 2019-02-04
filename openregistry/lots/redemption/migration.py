# -*- coding: utf-8 -*-
import logging

from openregistry.lots.core.migration import (
    BaseMigrationsRunner,
)


LOGGER = logging.getLogger(__name__)


class RedemptionMigrationsRunner(BaseMigrationsRunner):

    SCHEMA_VERSION = 1
    SCHEMA_DOC = 'openregistry_lots_redemption_schema'


MIGRATION_STEPS = []


def migrate(db):
    runner = RedemptionMigrationsRunner(db)
    runner.migrate(MIGRATION_STEPS)
