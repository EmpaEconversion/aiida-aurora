"""
Dummy CalcJobs to simulate a battery experiment.
"""
from aiida.common import datastructures
from aiida.engine import CalcJob
# from aiida.orm import SinglefileData
from aiida.orm import Dict

from aiida_aurora.data.battery import BatterySampleData
# TODO: from aiida_aurora.data.battery import BatteryStateData
from aiida_aurora.data.experiment import CyclingSpecsData


class BatteryFakeExperiment(CalcJob):
    """
    AiiDA calculation plugin for the fake_aurora_server script.

    Simple AiiDA plugin that sends input data as json files to the fake Aurora server API script.
    """

    _INPUT_BATTERY_JSON_FILE = "battery.json"
    _INPUT_EXPERIMENT_JSON_FILE = "experiment.json"
    _OUTPUT_JSON_FILE = "output.json"
    _DEFAULT_STDOUT_FILE = "output.log"

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        super().define(spec)

        # set default values for AiiDA options
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.inputs["metadata"]["options"]["parser_name"].default = "aurora"

        # new ports
        spec.input(
            "metadata.options.output_filename",
            valid_type=str,
            default=cls._DEFAULT_STDOUT_FILE,
        )
        spec.input("battery_sample", valid_type=BatterySampleData, help="Battery sample used.")
        spec.input("exp_specs", valid_type=CyclingSpecsData, help="Experiment specifications.")
        spec.output("results", valid_type=Dict, help="Results of the experiment.")  # a proper type should be defined
        # spec.output('battery_state', valid_type=BatteryStateData, help='State of the battery after the experiment.')

        spec.exit_code(
            300, "ERROR_MISSING_OUTPUT_FILES", message="Calculation did not produce all expected output files."
        )

    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files
            needed by the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        with open(self._INPUT_BATTERY_JSON_FILE, "w") as handle:
            handle.write(self.inputs.battery_sample.get_json())
        with open(self._INPUT_EXPERIMENT_JSON_FILE, "w") as handle:
            handle.write(self.inputs.exp_specs.get_json())

        codeinfo = datastructures.CodeInfo()
        # codeinfo.cmdline_params = self.inputs.parameters.cmdline_params(
        #     file1_name=self.inputs.file1.filename,
        #     file2_name=self.inputs.file2.filename)
        codeinfo.cmdline_params = [
            self._INPUT_BATTERY_JSON_FILE,
            self._INPUT_EXPERIMENT_JSON_FILE,
            "-o",
            self._OUTPUT_JSON_FILE,
        ]
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.retrieve_list = [
            self.metadata.options.output_filename,
            self._OUTPUT_JSON_FILE,
        ]

        return calcinfo
