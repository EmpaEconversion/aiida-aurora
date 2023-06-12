""" Tests for calculations

"""
from aiida.plugins import CalculationFactory, DataFactory


def test_entry_points():
    """Tests the loading of the entry points."""
    DataFactory("aurora.batterysample")
    DataFactory("aurora.batterystate")
    DataFactory("aurora.cyclingspecs")
    DataFactory("aurora.tomatosettings")

    CalculationFactory("aurora.fake")
    CalculationFactory("aurora.cycler")
