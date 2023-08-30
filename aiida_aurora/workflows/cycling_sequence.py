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

    reference_keys = set(inputs['protocols'].keys())
    for namekey in inputs['control_settings'].keys():

        if namekey not in reference_keys:
            error_message += f'namekey {namekey} missing in protocols\n'
            continue

        reference_keys.remove(namekey)

    for remaining_key in reference_keys:
        error_message += f'protocol {remaining_key} has no settings\n'

    if len(error_message) > 0:
        return error_message


class CyclingSequenceWorkChain(WorkChain):
    """This workflow represents a process containing a variable number of steps."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""

        super().define(spec)

        spec.input(
            "battery_sample",
            valid_type=BatterySampleData,
            help="Battery sample to be used.",
        )

        spec.input(
            "tomato_code",
            valid_type=orm.Code,
            help="Tomato code to use.",
        )

        spec.input_namespace(
            "protocols",
            dynamic=True,
            valid_type=CyclingSpecsData,
            help="List of experiment specifications.",
        )

        spec.input_namespace(
            "control_settings",
            dynamic=True,
            valid_type=TomatoSettingsData,
            help="List of experiment control settings.",
        )

        spec.input_namespace(
            "monitor_settings",
            dynamic=True,
            valid_type=orm.Dict,
            help="Dictionary of battery experiment monitor settings.",
        )

        spec.output_namespace(
            "results",
            dynamic=True,
            valid_type=orm.ArrayData,
            help="Results of each step by key.",
        )

        spec.inputs.validator = validate_inputs

        spec.outline(
            cls.setup_workload,
            while_(cls.has_steps_remaining)(
                cls.run_cycling_step,
                cls.inspect_cycling_step,
            ),
            cls.gather_results,
        )

        spec.exit_code(
            401,
            'ERROR_IN_CYCLING_STEP',
            message='One of the steps of CyclingSequenceWorkChain failed',
        )

    def setup_workload(self):
        """Take the inputs and wrap them together."""
        self.worksteps_keynames = list(self.inputs['protocols'].keys())

    def has_steps_remaining(self):
        """Check if there is any remaining step."""
        return len(self.worksteps_keynames) > 0

    def inspect_cycling_step(self):
        """Verify that the last cycling step finished successfully."""
        last_subprocess = self.ctx.subprocesses[-1]

        if not last_subprocess.is_finished_ok:
            pkid = last_subprocess.pk
            stat = last_subprocess.exit_status
            self.report(f'Cycling substep <pk={pkid}> failed with exit status {stat}')
            return self.exit_codes.ERROR_IN_CYCLING_STEP

    def run_cycling_step(self):
        """Run the next cycling step."""
        current_keyname = self.worksteps_keynames.pop(0)

        inputs = {
            'code': self.inputs.tomato_code,
            'battery_sample': self.inputs.battery_sample,
            'protocol': self.inputs.protocols[current_keyname],
            'control_settings': self.inputs.control_settings[current_keyname],
        }

        has_monitors = current_keyname in self.inputs.monitor_settings

        if has_monitors:
            inputs['monitors'] = self.inputs.monitor_settings[current_keyname]

        running = self.submit(CyclerCalcjob, **inputs)

        if has_monitors:
            running.set_extra('monitored', True)
        else:
            running.set_extra('monitored', False)

        self.report(f'launching CyclerCalcjob<{running.pk}>')
        return ToContext(subprocesses=append_(running))

    def gather_results(self):
        """Gather the results from all cycling steps."""
        keynames = list(self.inputs['protocols'].keys())
        if len(self.ctx.subprocesses) != len(keynames):
            raise RuntimeError('Problem with subprocess!')

        multiple_results = {}
        for keyname in keynames:
            current_subprocess = self.ctx.subprocesses.pop(0)
            if 'results' not in current_subprocess.outputs:
                continue
            multiple_results[keyname] = current_subprocess.outputs.results

        self.out('results', dict(multiple_results))
