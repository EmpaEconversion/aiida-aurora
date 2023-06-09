from datetime import datetime
from enum import Flag
from typing import Literal, Optional

from pydantic import BaseModel, NonNegativeFloat, PositiveFloat, root_validator

from .utils import extract_schema_types


class BatteryComposition(BaseModel):  # TypedDict?
    description: Optional[str] = None
    cathode: Optional[str] = None
    anode: Optional[str] = None
    electrolyte: Optional[str] = None

    class Config:
        # exclude fields from export, to avoid validation errors when reloaded
        fields = {
            'cathode': {
                'exclude': True
            },
            'anode': {
                'exclude': True
            },
            'electrolyte': {
                'exclude': True
            },
        }

    @root_validator
    def validate_composition(cls, values):
        """
        Check that components are not specified if 'description' is specified
        then build components from a 'description' string, or vice versa.
        # TODO: what to do if 'description' is not in the C|E|A format?
        """
        if values['description']:
            if any(values[key] for key in ('cathode', 'anode', 'electrolyte')):
                raise ValueError("You cannot specify a 'description' and any component at the same time.")
            values['description'] = values['description'].strip()
            components = list(map(str.strip, values['description'].split('|')))
            if len(components) == 3:
                values['cathode'], values['electrolyte'], values['anode'] = components
            else:
                values['cathode'], values['electrolyte'], values['anode'] = (None, None, None)
                # raise ValueError(
                # "Composition 'description' does not have 3 components (i.e. {cathode}|{electrolyte}|{anode}).")
        elif any(values[key] for key in ('cathode', 'anode', 'electrolyte')):
            for key in ('cathode', 'anode', 'electrolyte'):
                values[key] = values[key].strip()
            values['description'] = f"{values['cathode']}|{values['electrolyte']}|{values['anode']}"
        else:
            raise ValueError("You must specify either a string 'description' or the components.")
        return values


class BatteryCapacity(BaseModel):  # TypedDict?
    nominal: PositiveFloat
    actual: Optional[NonNegativeFloat]
    units: Literal["mAh", "Ah"]


class BatteryMetadata(BaseModel):
    name: str
    creation_datetime: datetime
    creation_process: str


class BatterySpecs(BaseModel):
    """
    Battery specification schema.
    """
    manufacturer: str
    composition: BatteryComposition
    form_factor: str
    capacity: BatteryCapacity

    # manufacturer, form_factor:
    # should we use a Literal or a validator to check that they are one of the available ones?

    # add pre-validator to specify capacity as str (e.g. '4.8 mAh')?


class BatterySample(BatterySpecs):
    """
    Battery sample schema.
    """
    battery_id: int
    metadata: BatteryMetadata


class ChargeState(Flag):
    """Defines the charge state of a battery."""
    CHARGED = True
    DISCHARGED = False


class BatteryState(BatterySample):
    """
    Battery state schema.
    """
    state_id: int
    charged: ChargeState = ChargeState.CHARGED


BatterySpecsJsonTypes = extract_schema_types(BatterySpecs)
BatterySampleJsonTypes = extract_schema_types(BatterySample)
