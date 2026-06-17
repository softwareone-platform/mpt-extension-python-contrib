from dataclasses import dataclass
from typing import override

import pytest
from mpt_extension_contrib.due_date import DueDateSettings
from mpt_extension_sdk.models.parameter import ParameterValue
from mpt_extension_sdk.settings.extension import BaseExtensionSettings


@dataclass(frozen=True)
class DueDateExtensionSettings(BaseExtensionSettings, DueDateSettings):
    due_date_parameter: str = "dueDate"

    @override
    @classmethod
    def load(cls):
        return cls()


@pytest.fixture
def extension_settings():
    return DueDateExtensionSettings()


@pytest.fixture
def due_date_parameter_factory():
    def factory(stored_value=None):
        return ParameterValue(external_id="dueDate", value=stored_value)

    return factory
