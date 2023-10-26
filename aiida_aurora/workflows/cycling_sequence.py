from aiida import orm
from aiida.engine import ToContext, WorkChain, append_, while_
from aiida.plugins import DataFactory

from aiida_aurora.calculations import BatteryCyclerExperiment

CyclingSpecsData = DataFactory('aurora.cyclingspecs')
BatterySampleData = DataFactory('aurora.batterysample')
TomatoSettingsData = DataFactory('aurora.tomatosettings')


def validate_inputs(inputs, ctx=None):
    """Validate the inputs of the entire input namespace."""
    error_message = ''

    reference_keys = set(inputs['protocol_order'])
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

        spec.input(
            "protocol_order",
            valid_type=orm.List,
            help="List of experiment protocol names in order of execution.",
        )

        spec.input(
            "group_label",
            valid_type=orm.Str,
            help="A label prefix for grouping experiments.",
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
        """Create an ordered list of protocol step names."""
        self.worksteps_keynames = list(self.inputs["protocol_order"])

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
        protocol_name = self.worksteps_keynames.pop(0)

        inputs = {
            'code': self.inputs.tomato_code,
            'battery_sample': self.inputs.battery_sample,
            'protocol': self.inputs.protocols[protocol_name],
            'control_settings': self.inputs.control_settings[protocol_name],
        }

        has_monitors = protocol_name in self.inputs.monitor_settings

        if has_monitors:
            inputs['monitors'] = self.inputs.monitor_settings[protocol_name]

        running = self.submit(BatteryCyclerExperiment, **inputs)
        sample_name = self.inputs.battery_sample.attributes["metadata"]["name"]
        running.label = f"{protocol_name} | {sample_name}"

        if has_monitors:
            running.set_extra('monitored', True)
        else:
            running.set_extra('monitored', False)

        workflow_group = self.inputs.group_label.value
        experiment_group = f"{workflow_group}/{protocol_name}"
        for group in (
            "all-experiments",
            protocol_name,
            workflow_group,
            experiment_group,
        ):
            self.add_to_group(running, group)

        self.report(f'launching BatteryCyclerExperiment<{running.pk}>')
        return ToContext(subprocesses=append_(running))

    def add_to_group(self, node: BatteryCyclerExperiment, label: str) -> None:
        """docstring"""
        group_label = f"aurora/experiments/{label}"
        orm.Group.collection.get_or_create(group_label)[0].add_nodes(node)

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
