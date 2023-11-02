####################################################################################################
"""Script to use as a template for the submission of the cycling sequence workchain."""
####################################################################################################
import datetime

from aiida import orm
from aiida.engine import calcfunction, submit
from aiida.plugins import DataFactory, WorkflowFactory

CyclingSpecsData = DataFactory('aurora.cyclingspecs')
BatterySampleData = DataFactory('aurora.batterysample')
TomatoSettingsData = DataFactory('aurora.tomatosettings')


@calcfunction
def generate_test_inputs():
    """Generate the inputs."""
    nodes_dict = {}

    nodes_dict['sample'] = BatterySampleData({
        'specs.manufacturer':
        'fake_maufacturer',
        'specs.composition':
        dict(description='C|E|A'),
        'specs.case':
        'fake_form',
        'specs.capacity':
        dict(nominal=1.0, units='Ah'),
        'id':
        666,
        'metadata':
        dict(
            name='commercial-10',
            creation_datetime=datetime.datetime.now(tz=datetime.timezone.utc),
            creation_process='This is a fake battery for testing purposes.'
        )
    })

    BASELINE_SPECS = {
        'method': [{
            'name': 'DUMMY_SEQUENTIAL_1',
            'device': 'worker',
            'technique': 'sequential',
            'parameters': {
                'time': {
                    'label': 'Time:',
                    'units': 's',
                    'value': 60.0,
                    'required': True,
                    'description': '',
                    'default_value': 100.0
                },
                'delay': {
                    'label': 'Delay:',
                    'units': 's',
                    'value': 1.0,
                    'required': True,
                    'description': '',
                    'default_value': 1.0
                }
            },
            'short_name': 'DUMMY_SEQUENTIAL',
            'description': 'Dummy worker - sequential numbers'
        }]
    }

    step1_tech = dict(BASELINE_SPECS)
    nodes_dict['step1_tech'] = CyclingSpecsData(step1_tech)
    step2_tech = dict(BASELINE_SPECS)
    step2_tech['method'][0]['parameters']['time']['value'] = 30.0
    nodes_dict['step2_tech'] = CyclingSpecsData(step2_tech)

    BASELINE_SETTINGS = {
        "output": {
            "path": None,
            "prefix": None
        },
        "snapshot": None,
        "verbosity": "INFO",
        "unlock_when_done": True,
    }

    nodes_dict['step1_setting'] = TomatoSettingsData(BASELINE_SETTINGS)
    nodes_dict['step2_setting'] = TomatoSettingsData(BASELINE_SETTINGS)

    return nodes_dict


####################################################################################################
# ACTUAL SUBMISSION

WorkflowClass = WorkflowFactory('aurora.cycling_sequence')
workflow_builder = WorkflowClass.get_builder()
workflow_inputs = generate_test_inputs()

workflow_builder.tomato_code = orm.load_code('ketchup-0.2rc2@localhost-tomato')

workflow_builder.battery_sample = workflow_inputs['sample']
workflow_builder.protocols = {
    'step1': workflow_inputs['step1_tech'],
    'step2': workflow_inputs['step2_tech'],
}
workflow_builder.control_settings = {
    'step1': workflow_inputs['step1_setting'],
    'step2': workflow_inputs['step2_setting'],
}

workflow_node = submit(workflow_builder)

####################################################################################################
