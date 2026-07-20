from dataclasses import dataclass
from typing import override

import pytest
from mpt_extension_contrib.phase_step import PhaseStepSettings
from mpt_extension_sdk.models.parameter import ParameterValue
from mpt_extension_sdk.settings.extension import BaseExtensionSettings


@dataclass(frozen=True)
class PhaseStepExtensionSettings(BaseExtensionSettings, PhaseStepSettings):
    phase_parameter: str = "phase"

    @override
    @classmethod
    def load(cls):
        return cls()


@pytest.fixture
def extension_settings():
    return PhaseStepExtensionSettings()


@pytest.fixture
def phase_parameter_factory():
    def factory(stored_value=None):
        return ParameterValue(external_id="phase", value=stored_value)

    return factory
