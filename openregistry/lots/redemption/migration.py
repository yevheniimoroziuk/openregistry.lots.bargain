# -*- coding: utf-8 -*-
import logging

from openregistry.lots.core.migration import (
    BaseMigrationsRunner,
)


LOGGER = logging.getLogger(__name__)


class BargainMigrationsRunner(BaseMigrationsRunner):

    SCHEMA_VERSION = 1
    SCHEMA_DOC = 'openregistry_lots_bargain_schema'


MIGRATION_STEPS = []


def migrate(db):
    runner = BargainMigrationsRunner(db)
    runner.migrate(MIGRATION_STEPS)
