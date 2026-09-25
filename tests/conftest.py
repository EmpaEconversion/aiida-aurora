"""pytest fixtures for simplified testing."""
import pytest

pytest_plugins = ["aiida.tools.pytest_fixtures"]


@pytest.fixture(scope="function", autouse=True)
def clear_database_auto(aiida_profile_clean):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""


@pytest.fixture(scope="function")
def aurora_code(aiida_code_installed):
    """Get a aurora code."""
    return aiida_code_installed(default_calc_job_plugin="aurora", filepath_executable="diff")
