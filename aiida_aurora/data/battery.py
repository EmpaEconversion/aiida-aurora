"""
Data types provided by plugin

Register data types via the "aiida.data" entry point in setup.json.
"""

import json

from aurora.schemas.data_schemas import BatterySample as BatterySampleSchema
from aurora.schemas.data_schemas import BatteryState as BatteryStateSchema
import yaml

from aiida.orm import Dict


class BatterySample(Dict):  # pylint: disable=too-many-ancestors
    """
    A battery sample data object.

    This class represents a battery sample.
    """

    # "pydantic" schema to add automatic validation
    schema = BatterySampleSchema

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
        if not self.label:
            self.label = self.dict["metadata"].get("name")

    def validate(self, parameters_dict):  # pylint: disable=no-self-use
        """Validate command line options.

        Uses the voluptuous package for validation. Find out about allowed keys using::

            print(BatterySample.schema)

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict
        :returns: validated dictionary
        """
        d = BatterySampleSchema(**parameters_dict).dict()
        # Manual fix to convert date-times to ISO string format
        # TODO integrate this into the data schema
        d["metadata"]["creation_datetime"] = d["metadata"][
            "creation_datetime"
        ].isoformat()
        return d

    def get_json(self):
        """Get a JSON file containing the BatterySample specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = self.get_dict()
        return json.dumps(object_to_be_serialized)

    def get_yaml(self):
        """Get a YAML file containing the BatterySample specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = {"sample": self.get_dict()}
        return yaml.dump(object_to_be_serialized)

    def __str__(self):
        """String representation of node.

        Append values of dictionary to usual representation. E.g.::

            uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
            {'ignore-case': True}
        """
        string = super().__str__()
        string += "\n" + str(self.get_dict())
        return string


class BatteryState(Dict):  # pylint: disable=too-many-ancestors
    """
    A battery state data object.

    This class represents a battery state.
    It consists of a battery sample and a state id.
    """

    # "pydantic" schema  to add automatic validation
    schema = BatteryStateSchema

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
        return BatteryStateSchema(parameters_dict).dict()

    def __str__(self):
        """String representation of node.

        Append values of dictionary to usual representation. E.g.::

            uuid: b416cbee-24e8-47a8-8c11-6d668770158b (pk: 590)
            {'ignore-case': True}
        """
        string = super().__str__()
        string += "\n" + str(self.get_dict())
        return string
