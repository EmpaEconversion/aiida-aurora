from aiida import orm
from aiida.engine import ToContext, WorkChain, append_, while_
from aiida.plugins import CalculationFactory, DataFactory

CyclerCalcjob = CalculationFactory('aurora.cycler')
CyclingSpecsData = DataFactory('aurora.cyclingspecs')
BatterySampleData = DataFactory('aurora.batterysample')
TomatoSettingsData = DataFactory('aurora.tomatosettings')


def validate_inputs(inputs, ctx=None):
    """Validate the inputs of the entire input namespace."""

    error_message = ''
    for namekey in inputs['techniques'].keys():
        if namekey not in inputs['control_settings']:
            error_message += f'namekey {namekey} missing in control_settings\n'

    for namekey in inputs['control_settings'].keys():
        if namekey not in inputs['techniques']:
            error_message += f'namekey {namekey} missing in techniques\n'

    if len(error_message) > 0:
        return error_message


class CyclingSequenceWorkChain(WorkChain):
    """This workflow represents a process containing a variable number of steps."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.input(
            "battery_sample",
            valid_type=BatterySampleData,
            help="Battery sample to be used."
        )
        spec.input(
            "tomato_code",
            valid_type=orm.Code,
            help="Tomato code to use."
        )

        spec.input_namespace(
            "techniques",
            dynamic=True,
            valid_type=CyclingSpecsData,
            help="List of experiment specifications."
        )
        spec.input_namespace(
            "control_settings",
            dynamic=True,
            valid_type=TomatoSettingsData,
            help="List of experiment control settings."
        )
        spec.output_namespace(
            "results",
            dynamic=True,
            valid_type=orm.ArrayData,
            help="Results of each step by key."
        )

        spec.outline(
            cls.setup_workload,
            while_(cls.has_steps_remaining)(
                cls.run_cycling_step,
            ),
            cls.gather_results,
        )

    def setup_workload(self):
        """Takes the inputs and wraps them together."""
        self.worksteps_keynames = list(self.inputs['techniques'].keys())

    def has_steps_remaining(self):
        """Checks if there is any remaining step"""
        return len(self.worksteps_keynames) > 0

    def run_cycling_step(self):
        """Description"""
        current_keyname = self.worksteps_keynames.pop(0)
        inputs = {
            'code': self.inputs.tomato_code,
            'battery_sample': self.inputs.battery_sample,
            'technique': self.inputs.techniques[current_keyname],
            'control_settings': self.inputs.control_settings[current_keyname],
        }
        running = self.submit(CyclerCalcjob, **inputs)
        self.report(f'launching CyclerCalcjob<{running.pk}>')
        return ToContext(workchains=append_(running))

    def gather_results(self):
        """Description"""
        keynames = list(self.inputs['techniques'].keys())
        if len(self.ctx.workchains) != len(keynames):
            raise RuntimeError('Problem with workchain!')

        multiple_results = {}
        for keyname in keynames:
            current_workchain = self.ctx.workchains.pop(0)
            if 'results' not in current_workchain.outputs:
                continue
            multiple_results[keyname] = current_workchain.outputs.results

        self.out('results', dict(multiple_results))
