"""
A dummy experiment specifications class.
"""
import json

import yaml

from aiida.orm import Dict

from aiida_aurora.schemas.dgbowl import conversion_map

TOMATO_PAYLOAD_VERSION = "0.2"
TomatoSchema = conversion_map[TOMATO_PAYLOAD_VERSION]["tomato"]


class TomatoSettingsData(Dict):  # pylint: disable=too-many-ancestors
    """
    An experiment specification object.

    This class represents the specifications used in an experiment.
    """

    # "pydantic" schema  to add automatic validation
    schema = TomatoSchema

    # pylint: disable=redefined-builtin
    def __init__(self, dict=None, **kwargs):
        """
        Constructor for the data class

        Usage: ``TomatoSettingsData(dict{...})``

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict
        """
        dict = self.validate(dict)
        super().__init__(dict=dict, **kwargs)
        # if not self.label:
        #     self.label = self.dict['metadata'].get('name')

    def validate(self, parameters_dict):  # pylint: disable=no-self-use
        """Validate command line options.

        Uses the voluptuous package for validation. Find out about allowed keys using::

            print(TomatoSettingsData.schema)

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict
        :returns: validated dictionary
        """
        return TomatoSchema(**parameters_dict).dict()

    def get_json(self):
        """Get a JSON file containing the DummyExperimentSpecs specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = self.get_dict()
        return json.dumps(object_to_be_serialized)

    def get_yaml(self):
        """Get a YAML file containing the TomatoSettingsData specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = {"tomato": self.get_dict()}
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
