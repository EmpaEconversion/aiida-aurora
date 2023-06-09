####################################################################################################
"""Script to use as a template for the submission of the stress test."""
####################################################################################################
import datetime
import json
from typing import Any, Dict, List

from aurora.schemas.battery import BatterySample as BatterySampleSchema

from aiida import orm
from aiida.engine import submit
from aiida.plugins import WorkflowFactory

from aiida_aurora.data import BatterySampleData

BATTERIES_SPECIFICATIONS_LOCAL = [
    BatterySampleSchema(
        manufacturer='fake',
        composition=dict(description='C|E|A'),
        form_factor='DUMB',
        capacity=dict(nominal=1.0, units='Ah'),
        battery_id=666,
        metadata=dict(
            name='fake_sample01',
            creation_datetime=datetime.datetime.now(tz=datetime.timezone.utc),
            creation_process='This is a fake battery for testing purposes.'
        )
    ),
    BatterySampleSchema(
        manufacturer='fake',
        composition=dict(description='C|E|A'),
        form_factor='DUMB',
        capacity=dict(nominal=1.0, units='Ah'),
        battery_id=667,
        metadata=dict(
            name='fake_sample02',
            creation_datetime=datetime.datetime.now(tz=datetime.timezone.utc),
            creation_process='This is a fake battery for testing purposes.'
        )
    ),
]

MONITOR_OVERRIDES: Dict[Any, Any] = {}

TOMATO_OVERRIDES: Dict[Any, Any] = {
    'protection_cycle': {},
    'formation_cycle': {},
    'longterm_cycle': {},
    'discharge_cycle': {},
}

PROTECTION_CYCLE_OVERSTEPS: List[Any] = [{}, {}, {}]
FORMATION_CYCLE_OVERSTEPS: List[Any] = [{}, {}, {}]
LONGTERM_CYCLE_OVERSTEPS: List[Any] = [{}, {}, {}]
DISCHARGE_CYCLE_OVERSTEPS: List[Any] = [{}]

CYCLER_OVERRIDES = {
    'protection_cycle': {
        'method': PROTECTION_CYCLE_OVERSTEPS
    },
    'formation_cycle': {
        'method': FORMATION_CYCLE_OVERSTEPS
    },
    'longterm_cycle': {
        'method': LONGTERM_CYCLE_OVERSTEPS
    },
    'discharge_cycle': {
        'method': DISCHARGE_CYCLE_OVERSTEPS
    },
}


####################################################################################################
def main_script():
    """Main script"""
    cycler_code = orm.load_code('ketchup-0.2rc2@localhost-tomato')
    monitor_code = orm.load_code('monitor@localhost-aiida')

    batteries_specifications = BATTERIES_SPECIFICATIONS_LOCAL
    # batteries_specifications = read_specifications('batteries.json')

    for battery_specification in batteries_specifications:
        print(battery_specification)
        continue
        sample_node = getmake_sample(battery_specification)

        WorkflowClass = WorkflowFactory('aurora.stress_test')
        workflow_builder = WorkflowClass.get_builder_from_protocol(
            ketchup_code=cycler_code,
            monitor_code=monitor_code,
            battery_sample=sample_node,
            tomato_overrides=TOMATO_OVERRIDES,
            cycler_overrides=CYCLER_OVERRIDES,
            monitor_overrides=MONITOR_OVERRIDES,
        )
        workflow_node = submit(workflow_builder)

        workflow_pk = workflow_node.pk
        battery_name = battery_specification.metadata.name
        print(f'Workflow <{workflow_pk}> submitted for battery `{battery_name}` ... ')


####################################################################################################
def getmake_sample(battery_schema):
    """Gets the sample node from the DB or creates it."""
    battery_name = battery_schema.metadata.name
    queryb = orm.QueryBuilder()
    queryb.append(orm.Group, filters={'label': {'==': 'BatterySamples'}}, tag='group0')
    queryb.append(
        BatterySampleData,
        filters={'attributes.metadata.name': {
            '==': battery_name
        }},
        with_group='group0',
    )

    battery_sample = queryb.first()
    if battery_sample is None:
        battery_sample = BatterySampleData(battery_schema.dict())

    return battery_sample


####################################################################################################
def read_specifications(source_filepath):
    """Reads the battery specifications from a json file"""

    with open(source_filepath) as fileobj:
        battery_datalist = json.load(fileobj)

    batteries_specifications = []
    for battery_data in battery_datalist:
        battery_sample = BatterySampleSchema(**battery_data)
        batteries_specifications.append(battery_sample)

    return batteries_specifications


####################################################################################################
if __name__ == "__main__":
    main_script()
####################################################################################################
