# -*- coding: utf-8 -*-
"""
Data types provided by plugin

Register data types via the "aiida.data" entry point in setup.json.
"""

from enum import Flag
import json
from voluptuous import Schema, Optional
from aiida.orm import Dict


class ChargeState(Flag):
    """Defines the charge state of a battery."""
    CHARGED = True
    DISCHARGED = False


# yapf: disable
batterysample_specs = {
    'description': {
        'electrode': str,               # electrode material
        'initial_state': ChargeState,   # initial state (charged/discharged)
        'electrolyte': str,             # electrolyte material
        Optional('comments'): str,      # comments
    },
    'parameters': {
        'C_Ah': float,      # battery capacity [Ah]
        'm_g': float,       # mass of active material [g]
        'Mw_gmol': float,   # molecular wright of active material [g/mol]
        'Aw_gmol': float,   # atomic weight of intercalated ion [g/mol]
        'N': int,           # number of electrons transferred per intercalated ion
        'dQ': float,        # theoretical capacity [Ah], dQ = N * (m/Mw) * (e * NA), convert from kC to Ah
    },
    'sample_id': 'str',     # battery (unique?) ID (optional?)
}

batterystate_specs = {
    'sample': batterysample_specs.copy(),
    'state_id': int,
}
# yapf: enable


class BatterySample(Dict):  # pylint: disable=too-many-ancestors
    """
    A battery sample data object.

    This class represents a battery sample.
    """

    # "voluptuous" schema  to add automatic validation
    schema = Schema(batterysample_specs)

    # pylint: disable=redefined-builtin
    def __init__(self, dict=None, **kwargs):
        """
        Constructor for the data class

        Usage: ``BatterySample(dict{...})``

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict

        """
        dict = self.validate(dict)
        super().__init__(dict=dict, **kwargs)

    def validate(self, parameters_dict):  # pylint: disable=no-self-use
        """Validate command line options.

        Uses the voluptuous package for validation. Find out about allowed keys using::

            print(BatterySample.schema)

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict
        :returns: validated dictionary
        """
        return BatterySample.schema(parameters_dict)

    def get_json(self):
        """Get a JSON file containing the BatterySample specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = self.get_dict()
        return json.dumps(object_to_be_serialized)


#    def cmdline_params(self, file1_name, file2_name):
#        """Synthesize command line parameters.
#
#        e.g. [ '--ignore-case', 'filename1', 'filename2']
#
#        :param file_name1: Name of first file
#        :param type file_name1: str
#        :param file_name2: Name of second file
#        :param type file_name2: str
#
#        """
#        parameters = []
#
#        pm_dict = self.get_dict()
#        for k in pm_dict.keys():
#            if pm_dict[k]:
#                parameters += ['--' + k]
#
#        parameters += [file1_name, file2_name]
#
#        return [str(p) for p in parameters]

    def __str__(self):
        """String representation of node.

        Append values of dictionary to usual representation. E.g.::

            uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
            {'ignore-case': True}

        """
        string = super().__str__()
        string += '\n' + str(self.get_dict())
        return string


class BatteryState(Dict):  # pylint: disable=too-many-ancestors
    """
    A battery state data object.

    This class represents a battery state.
    It consists of a battery sample and a state id.
    """

    # "voluptuous" schema  to add automatic validation
    schema = Schema(batterystate_specs)

    # pylint: disable=redefined-builtin
    def __init__(self, dict=None, **kwargs):
        """
        Constructor for the data class

        Usage: ``BatteryState(dict{...})``

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict

        """
        dict = self.validate(dict)
        super().__init__(dict=dict, **kwargs)

    def validate(self, parameters_dict):  # pylint: disable=no-self-use
        """Validate command line options.

        Uses the voluptuous package for validation. Find out about allowed keys using::

            print(BatteryState.schema)

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict
        :returns: validated dictionary
        """
        return BatteryState.schema(parameters_dict)

    def __str__(self):
        """String representation of node.

        Append values of dictionary to usual representation. E.g.::

            uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
            {'ignore-case': True}

        """
        string = super().__str__()
        string += '\n' + str(self.get_dict())
        return string
