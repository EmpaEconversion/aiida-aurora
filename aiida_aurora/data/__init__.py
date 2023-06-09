"""
Data types provided by plugin

Register data types via the "aiida.data" entry point in setup.json.
"""

from .battery import BatterySampleData, BatteryStateData
from .control import TomatoSettingsData
from .experiment import CyclingSpecsData

__all__ = [
    'BatterySampleData',
    'BatteryStateData',
    'TomatoSettingsData',
    'CyclingSpecsData',
]
