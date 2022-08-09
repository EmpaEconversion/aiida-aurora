"""
Data types provided by plugin

Register data types via the "aiida.data" entry point in setup.json.
"""

from .battery import BatterySample, BatteryState
from .control import TomatoSettings
from .experiment import CyclingSpecs
