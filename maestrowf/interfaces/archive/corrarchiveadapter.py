"""
The CoRR archive adapter transforms the Maestro workflow specification to the
CoRR data schema to archive Maestro runs.

Note: This is a prototype.
"""
import os
import logging

from maestrowf.abstracts.interfaces import ArchiveAdapter


LOGGER = logging.getLogger(__name__)

class CorrHttpAdapter(ArchiveAdapter):
    """
    Adatper for sending Maestro specification data to CoRR. This implementation
    is based on:
    https://github.com/usnistgov/corr-sumatra/blob/corr-integrate/sumatra/recordstore/http_store.py#L231
    """
    def __init__(self):
        pass

    def _get(self):
        pass

    def _post(self):
        pass

    def create_project(self):
        pass

    def has_project(self):
        pass
