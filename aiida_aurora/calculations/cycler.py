"""
Calculations provided by aiida_aurora.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
from importlib import import_module

import yaml

from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import ArrayData, SinglefileData

from aiida_aurora.data.battery import BatterySample, BatteryState
from aiida_aurora.data.control import TomatoSettings
from aiida_aurora.data.experiment import CyclingSpecs


class BatteryCyclerExperiment(CalcJob):
    """
    AiiDA calculation plugin for the tomato instrument automation package.
    https://github.com/dgbowl/tomato
    """
    _INPUT_PAYLOAD_YAML_FILE = 'payload.yaml'
    _INPUT_PAYLOAD_VERSION = '0.2'
    _OUTPUT_FILE_PREFIX = 'results'

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
        # spec.inputs['metadata']['options']['scheduler_stderr'].default = ''
        # spec.inputs['metadata']['options']['scheduler_stdout'].default = ''

        # new ports
        spec.input('metadata.options.output_filename', valid_type=str, default=cls._OUTPUT_FILE_PREFIX)
        spec.input('battery_sample', valid_type=BatterySample, help='Battery sample used.')
        spec.input('technique', valid_type=CyclingSpecs, help='Experiment specifications.')
        spec.input('control_settings', valid_type=TomatoSettings, help='Experiment control settings.')
        spec.output('results', valid_type=ArrayData, help='Results of the experiment.')
        spec.output('raw_data', valid_type=SinglefileData, help='Raw data retrieved.')
        # spec.output('battery_state', valid_type=BatteryState, help='State of the battery after the experiment.')

        spec.exit_code(300, 'ERROR_MISSING_OUTPUT_FILES', message='Experiment did not produce any kind of output file.')
        spec.exit_code(301, 'ERROR_MISSING_JSON_FILE', message='Experiment did not produce an output json file.')
        spec.exit_code(302, 'ERROR_MISSING_ZIP_FILE', message='Experiment did not produce a zip file with raw data.')
        spec.exit_code(311, 'ERROR_COMPLETED_ERROR', message='The tomato job was marked as completed with an error.')
        spec.exit_code(312, 'ERROR_COMPLETED_CANCELLED', message='The tomato job was marked as cancelled.')
        spec.exit_code(400, 'ERROR_PARSING_JSON_FILE', message='Parsing of json file failed.')

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        # if connecting to a Windows PowerShell computer, change the extension of the submit script to '.ps1'
        if self.inputs.code.computer.transport_type == 'sshtowin':
            submit_script_filename = self.node.get_option('submit_script_filename')
            if not submit_script_filename.endswith('.ps1'):
                if submit_script_filename.endswith('.sh'):
                    submit_script_filename = submit_script_filename[:-3] + '.ps1'
                else:
                    submit_script_filename(submit_script_filename + '.ps1')
                self.node.backend_entity.set_attribute('submit_script_filename', submit_script_filename)

        # prepare the payload
        # TODO: use dgbowl_schemas module
        ## from dgbowl_schemas.tomato.payload_0_1.tomato import Tomato
        ## - should 'version: "0.1"' be written in the submit script?
        ## - name of the file containing the sample and method
        tomato_schema_module = import_module(f"aurora.schemas.tomato_{self._INPUT_PAYLOAD_VERSION.replace('.', 'p')}")
        TomatoSchema = tomato_schema_module.tomato.Tomato

        tomato_dict = self.inputs.control_settings.get_dict()
        if tomato_dict['output']['prefix'] is None:
            tomato_dict['output']['prefix'] = self._OUTPUT_FILE_PREFIX
        else:
            self._OUTPUT_FILE_PREFIX = tomato_dict['output']['prefix']
        payload = tomato_schema_module.TomatoPayload(
            version = self._INPUT_PAYLOAD_VERSION,
            sample = tomato_schema_module.sample.convert_batterysample_to_sample(self.inputs.battery_sample.get_dict()),
            method = tomato_schema_module.method.convert_electrochemsequence_to_method_list(
                self.inputs.technique.get_dict()),
            tomato = TomatoSchema(**tomato_dict),
        )
        with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
            handle.write(yaml.dump(payload.dict()))

        codeinfo = datastructures.CodeInfo()

        # the calculation code should be 'ketchup', so we add the following `cmdline_params`
        # in order to submit the payload to tomato
        codeinfo.cmdline_params = ['submit', '--jobname', '$JOB_TITLE', self._INPUT_PAYLOAD_YAML_FILE]
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.retrieve_list = [f'{self._OUTPUT_FILE_PREFIX}.json']
        calcinfo.retrieve_temporary_list = [f'{self._OUTPUT_FILE_PREFIX}.zip']

        return calcinfo
