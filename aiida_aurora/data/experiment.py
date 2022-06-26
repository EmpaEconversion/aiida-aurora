# -*- coding: utf-8 -*-
"""
A dummy experiment specifications class.
"""

import json, yaml
from aurora.schemas.cycling import ElectroChemSequence as ElectroChemSequenceSchema
from aiida.orm import Dict


class CyclingSpecs(Dict):  # pylint: disable=too-many-ancestors
    """
    An experiment specification object.

    This class represents the specifications used in an experiment.
    """

    # "pydantic" schema  to add automatic validation
    schema = ElectroChemSequenceSchema

    # pylint: disable=redefined-builtin
    def __init__(self, dict=None, **kwargs):
        """
        Constructor for the data class

        Usage: ``DummyExperimentSpecs(dict{...})``

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

            print(DummyExperimentSpecs.schema)

        :param parameters_dict: dictionary with battery specifications
        :param type parameters_dict: dict
        :returns: validated dictionary
        """
        return ElectroChemSequenceSchema(**parameters_dict).dict()

    def get_json(self):
        """Get a JSON file containing the DummyExperimentSpecs specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = self.get_dict()
        return json.dumps(object_to_be_serialized)

    def get_yaml(self):
        """Get a YAML file containing the BatterySample specs."""

        # this can be customized to fit the desired format
        object_to_be_serialized = {'method': self.get_dict()}
        return yaml.dump(object_to_be_serialized)


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
