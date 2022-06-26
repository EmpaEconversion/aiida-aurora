# -*- coding: utf-8 -*-
"""
Calculations provided by aiida_aurora.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
from ast import Str
from aiida.common import datastructures
from aiida.engine import CalcJob
# from aiida.orm import SinglefileData
from aiida.orm import Dict, Str
# from aiida.plugins import DataFactory
from aiida_aurora.data.battery import BatterySample, BatteryState
from aiida_aurora.data.experiment import CyclingSpecs
import yaml, json


class BatteryCycler(CalcJob):
    """
    AiiDA calculation plugin for the tomato instrument automation package.
    https://github.com/dgbowl/tomato
    """
    _INPUT_PAYLOAD_YAML_FILE = 'payload.yaml'
    _INPUT_PAYLOAD_VERSION = '0.1'
    _OUTPUT_JSON_FILE = 'output.json'
    _OUTPUT_ZIP_FILE = 'output.zip'

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        # yapf: disable
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs['metadata']['options']['resources'].default = {  # REQUIRED?
            'num_machines': 1,
        }
        spec.inputs['metadata']['options']['parser_name'].default = 'aurora'
        spec.inputs['metadata']['options']['withmpi'].default = False
        spec.inputs['metadata']['options']['input_filename'].default = cls._INPUT_PAYLOAD_YAML_FILE
        # spec.inputs['metadata']['options']['output_filename'].default = None

        # new ports
        spec.input('battery_sample', valid_type=BatterySample, help='Battery sample used.')
        #spec.output('battery_state', valid_type=BatteryState, help='State of the battery before the experiment.')
        spec.input('technique', valid_type=CyclingSpecs, help='Experiment specifications.')
        spec.output('results', valid_type=Dict, help='Results of the experiment.')  # a proper type should be defined
        spec.output('battery_state', valid_type=BatteryState, help='State of the battery after the experiment.')

        spec.exit_code(300, 'ERROR_MISSING_OUTPUT_FILES', message='Calculation did not produce all expected output files.')

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
            handle.write(yaml.dump({'version': self._INPUT_PAYLOAD_VERSION}))
            handle.write(self.inputs.battery_sample.get_yaml())
            handle.write(self.inputs.technique.get_yaml())
            # TODO: integrate the dgbowl Tomato schema here, maybe add these options to the input metadata.options
            handle.write(yaml.dump({
                'tomato': {
                    'verbosity': 'DEBUG',
                    'unlock_when_done': True,
                    # "output": {
                    #     "prefix": None,
                    #     "path": None
                    # }
                }}))

        # TODO: read the payload version and load the appropriate schema
        # from dgbowl_schemas.tomato.payload_0_1.tomato import Tomato
        # - should 'version: "0.1"' be written in the submit script?
        # - name of the file containing the sample and method
        # PAYLOAD v 0.1 has everything in one file... but tomato and sample/method should be divided

        codeinfo = datastructures.CodeInfo()

        # the calculation code should be 'ketchup', so we add the following `cmdline_params`
        # in order to submit the payload to tomato
        codeinfo.cmdline_params = ['submit', self._INPUT_PAYLOAD_YAML_FILE]
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.retrieve_list = [self._OUTPUT_JSON_FILE]
        calcinfo.retrieve_singlefile_list = [('raw_data', 'singlefile', self._OUTPUT_ZIP_FILE)]

        return calcinfo
