"""Description
"""
import json
import pathlib

from pydantic.utils import deep_update

from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import ToContext, WorkChain
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory

TomatoCalcjob = CalculationFactory('aurora.cycler')
CyclingSpecsData = DataFactory('aurora.cyclingspecs')
BatterySampleData = DataFactory('aurora.batterysample')
TomatoSettingsData = DataFactory('aurora.tomatosettings')

CalcjobMonitor = WorkflowFactory('calcmonitor.monitor_wrapper')
TomatoMonitorData = DataFactory('calcmonitor.monitor.tomatobiologic')

BASEPATH = pathlib.Path(__file__).parent.resolve()
with open(f'{BASEPATH}/stress_test_defaults.json') as fileobj:
    ALL_DEFAULTS = json.load(fileobj)

DEFAULT_TOMATO_SETTINGS = ALL_DEFAULTS['DEFAULT_TOMATO_SETTINGS']
DEFAULT_MONITOR_PROTOCOL = ALL_DEFAULTS['DEFAULT_MONITOR_PROTOCOL']
DEFAULT_PROTECTION_METHOD = ALL_DEFAULTS['DEFAULT_PROTECTION_METHOD']
DEFAULT_FORMATION_METHOD = ALL_DEFAULTS['DEFAULT_FORMATION_METHOD']
DEFAULT_LONGTERM_METHOD = ALL_DEFAULTS['DEFAULT_LONGTERM_METHOD']
DEFAULT_DISCHARGE_METHOD = ALL_DEFAULTS['DEFAULT_DISCHARGE_METHOD']


class StressTestWorkChain(WorkChain):
    """Description."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        # yapf: disable
        super().define(spec)
        spec.expose_inputs(TomatoCalcjob, namespace='protection_cycle', exclude=('battery_sample',))
        spec.expose_inputs(TomatoCalcjob, namespace='formation_cycle', exclude=('battery_sample',))
        spec.expose_inputs(TomatoCalcjob, namespace='longterm_cycle', exclude=('battery_sample',))
        spec.expose_inputs(TomatoCalcjob, namespace='discharge_cycle', exclude=('battery_sample',))
        spec.expose_inputs(CalcjobMonitor, namespace='monitor')

        spec.input("battery_sample", valid_type=BatterySampleData, help="Battery sample used.")

        spec.outline(
            cls.run_protection_precycle,
            cls.run_formation_cycle,
            cls.run_longterm_cycling,
            cls.run_discharge_procedure,
            cls.gather_results,
        )

        spec.output("results_protection", valid_type=orm.ArrayData, help="Results of the protection step.")
        spec.output("results_formation", valid_type=orm.ArrayData, help="Results of the formation step.")
        spec.output("results_cycling", valid_type=orm.ArrayData, help="Results of the main cycling experiment.")
        spec.output("results_discharge", valid_type=orm.ArrayData, help="Results of the final discharge.")

        spec.exit_code(
            501,
            "WARNING_CHARGED_SAMPLE",
            message="The battery sample was not correctly discharged after the procedure."
        )

        # yapf: enable

    @classmethod
    def get_builder_from_protocol(
        cls,
        ketchup_code=None,
        monitor_code=None,
        battery_sample=None,
        tomato_overrides=None,
        cycler_overrides=None,
        monitor_overrides=None,
        protocol=None,
        overrides=None,
        **kwargs
    ):
        """
        Return a builder prepopulated with inputs selected according to the chosen protocol.
        """
        workchain_builder = cls.get_builder()

        if tomato_overrides is None:
            tomato_overrides = {}

        if cycler_overrides is None:
            tomato_overrides = {}

        # protection_cycle
        tomato_settings_dict = DEFAULT_TOMATO_SETTINGS
        if 'protection_cycle' in tomato_overrides:
            tomato_overrides_dict = tomato_overrides['protection_cycle']
            tomato_settings_dict = deep_update(tomato_settings_dict, tomato_overrides_dict)

        cycler_method_dict = DEFAULT_PROTECTION_METHOD
        if 'protection_cycle' in cycler_overrides:
            cycler_overrides_dict = cycler_overrides['protection_cycle']
            cycler_method_dict = mydeep_update(cycler_method_dict, cycler_overrides_dict)

        builder = TomatoCalcjob.get_builder()
        builder.code = ketchup_code
        builder.technique = CyclingSpecsData(cycler_method_dict)
        builder.control_settings = TomatoSettingsData(tomato_settings_dict)
        workchain_builder.protection_cycle = builder

        # formation_cycle
        tomato_settings_dict = DEFAULT_TOMATO_SETTINGS
        if 'formation_cycle' in tomato_overrides:
            tomato_overrides_dict = tomato_overrides['formation_cycle']
            tomato_settings_dict = deep_update(tomato_settings_dict, tomato_overrides_dict)

        cycler_method_dict = DEFAULT_FORMATION_METHOD
        if 'formation_cycle' in cycler_overrides:
            cycler_overrides_dict = cycler_overrides['formation_cycle']
            cycler_method_dict = mydeep_update(cycler_method_dict, cycler_overrides_dict)

        builder = TomatoCalcjob.get_builder()
        builder.code = ketchup_code
        builder.technique = CyclingSpecsData(cycler_method_dict)
        builder.control_settings = TomatoSettingsData(tomato_settings_dict)
        workchain_builder.formation_cycle = builder

        # longterm_cycle (monitor)
        tomato_settings_dict = DEFAULT_TOMATO_SETTINGS
        if 'longterm_cycle' in tomato_overrides:
            tomato_overrides_dict = tomato_overrides['longterm_cycle']
            tomato_settings_dict = deep_update(tomato_settings_dict, tomato_overrides_dict)

        cycler_method_dict = DEFAULT_LONGTERM_METHOD
        if 'longterm_cycle' in cycler_overrides:
            cycler_overrides_dict = cycler_overrides['longterm_cycle']
            cycler_method_dict = mydeep_update(cycler_method_dict, cycler_overrides_dict)

        builder = TomatoCalcjob.get_builder()
        builder.code = ketchup_code
        builder.technique = CyclingSpecsData(cycler_method_dict)
        builder.control_settings = TomatoSettingsData(tomato_settings_dict)
        workchain_builder.longterm_cycle = builder

        monitor_protocol_dict = DEFAULT_MONITOR_PROTOCOL
        if monitor_overrides is not None:
            monitor_protocol_dict = deep_update(monitor_protocol_dict, monitor_overrides)

        monitor_builder = CalcjobMonitor.get_builder()
        monitor_builder.code = monitor_code
        monitor_builder.metadata.options.parser_name = "calcmonitor.cycler"
        monitor_protocol = TomatoMonitorData(dict=monitor_protocol_dict)
        monitor_builder.monitor_protocols = {'monitor1': monitor_protocol}
        workchain_builder.monitor = monitor_builder

        # discharge_cycle
        tomato_settings_dict = DEFAULT_TOMATO_SETTINGS
        tomato_settings_dict['unlock_when_done'] = False
        if 'discharge_cycle' in tomato_overrides:
            tomato_overrides_dict = tomato_overrides['discharge_cycle']
            tomato_settings_dict = deep_update(tomato_settings_dict, tomato_overrides_dict)

        cycler_method_dict = DEFAULT_DISCHARGE_METHOD
        if 'discharge_cycle' in cycler_overrides:
            cycler_overrides_dict = cycler_overrides['discharge_cycle']
            cycler_method_dict = mydeep_update(cycler_method_dict, cycler_overrides_dict)

        builder = TomatoCalcjob.get_builder()
        builder.code = ketchup_code
        builder.technique = CyclingSpecsData(cycler_method_dict)
        builder.control_settings = TomatoSettingsData(tomato_settings_dict)
        workchain_builder.discharge_cycle = builder

        return workchain_builder

    def run_protection_precycle(self):
        """TODO."""
        calcjob_dictin = self.exposed_inputs(TomatoCalcjob, namespace='protection_cycle')
        calcjob_inputs = AttributeDict(calcjob_dictin)
        battery_sample = self.inputs.battery_sample
        battery_name = battery_sample.attributes['metadata']['name']
        calcjob_inputs.sample = battery_sample
        calcjob_node = self.submit(TomatoCalcjob, **calcjob_inputs)
        self.report(f'launching protection cycle <{calcjob_node.pk}> for sample `{battery_name}`')
        return ToContext(protection_cycle_calcjob=calcjob_node)

    def run_formation_cycle(self):
        """TODO."""
        calcjob_dictin = self.exposed_inputs(TomatoCalcjob, namespace='formation_cycle')
        calcjob_inputs = AttributeDict(calcjob_dictin)
        battery_sample = self.inputs.battery_sample
        battery_name = battery_sample.attributes['metadata']['name']
        calcjob_inputs.sample = battery_sample
        calcjob_node = self.submit(TomatoCalcjob, **calcjob_inputs)
        self.report(f'launching formation cycle <{calcjob_node.pk}> for sample `{battery_name}`')
        return ToContext(formation_cycle_calcjob=calcjob_node)

    def run_longterm_cycling(self):
        """TODO."""
        calcjob_dictin = self.exposed_inputs(TomatoCalcjob, namespace='longterm_cycle')
        calcjob_inputs = AttributeDict(calcjob_dictin)
        battery_sample = self.inputs.battery_sample
        battery_name = battery_sample.attributes['metadata']['name']
        calcjob_inputs.sample = battery_sample
        calcjob_node = self.submit(TomatoCalcjob, **calcjob_inputs)
        self.report(f'launching longterm cycle <{calcjob_node.pk}> for sample `{battery_name}`')

        monitor_dictin = self.exposed_inputs(CalcjobMonitor, namespace='monitor')
        monitor_inputs = AttributeDict(monitor_dictin)
        monitor_inputs.target_uuid = orm.Str(calcjob_node.uuid)
        monitor_inputs.calcjob.metadata.options.parser_name = "calcmonitor.cycler"
        monitor_node = self.submit(CalcjobMonitor, **monitor_inputs)
        self.report(f'launching monitor <{monitor_node.pk}> to control calcjob <{calcjob_node.pk}>')

        return ToContext(longterm_cycle_calcjob=calcjob_node, monitor_workflow=monitor_node)

    def run_discharge_cycle(self):
        """TODO."""
        calcjob_dictin = self.exposed_inputs(TomatoCalcjob, namespace='discharge_cycle')
        calcjob_inputs = AttributeDict(calcjob_dictin)
        battery_sample = self.inputs.battery_sample
        battery_name = battery_sample.attributes['metadata']['name']
        calcjob_inputs.sample = battery_sample
        calcjob_node = self.submit(TomatoCalcjob, **calcjob_inputs)
        self.report(f'launching discharge cycle <{calcjob_node.pk}> for sample `{battery_name}`')
        return ToContext(discharge_cycle_calcjob=calcjob_node)

    def gather_results(self):
        """TODO."""
        protection_cycle_calcjob = self.ctx.protection_cycle_calcjob
        formation_cycle_calcjob = self.ctx.formation_cycle_calcjob
        longterm_cycle_calcjob = self.ctx.longterm_cycle_calcjob
        monitor_workflow = self.ctx.monitor_workflow
        discharge_cycle_calcjob = self.ctx.discharge_cycle_calcjob

        if protection_cycle_calcjob.is_finished_ok:
            self.out('results_protection', protection_cycle_calcjob.outputs.results)

        if formation_cycle_calcjob.is_finished_ok:
            self.out('results_formation', formation_cycle_calcjob.outputs.results)

        if longterm_cycle_calcjob.is_finished_ok:
            self.out('results_cycling', longterm_cycle_calcjob.outputs.results)
        elif longterm_cycle_calcjob.is_killed and monitor_workflow.calcjob.is_finished_ok:
            self.out('results_cycling', monitor_workflow.calcjob.outputs.results)

        if discharge_cycle_calcjob.is_finished_ok:
            self.out('results_discharge', discharge_cycle_calcjob.outputs.results)
        else:
            return self.exit_codes.WARNING_CHARGED_SAMPLE


####################################################################################################
def mydeep_update(protocol_basis, protocol_overrides):
    """Extension of deep update to enter inside each method"""
    method_basis = protocol_basis['method']
    method_overrides = protocol_overrides['method']

    steps0 = len(method_basis)
    steps = len(method_overrides)
    if steps0 != steps:
        raise ValueError(f"One of the overrides must have {steps0} steps instead of {steps} (leave steps empty).")

    new_method = []
    for step_basis, step_override in zip(method_basis, method_overrides):
        new_step = deep_update(step_basis, step_override)
        new_method.append(new_step)

    return {'method': new_method}


####################################################################################################
