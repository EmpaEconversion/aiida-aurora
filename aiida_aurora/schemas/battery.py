from datetime import datetime
from enum import Flag
from typing import Literal, Optional, Set

from pydantic import BaseModel, NonNegativeFloat, PositiveInt

from .utils import extract_schema_types


class Component(BaseModel):
    description: Optional[str]


class Diameter(BaseModel):
    nominal: NonNegativeFloat
    actual: Optional[NonNegativeFloat]
    units: Literal["mm"] = "mm"


class Capacity(BaseModel):
    nominal: NonNegativeFloat
    actual: Optional[NonNegativeFloat]
    units: Literal["mAh", "Ah"] = "mAh"


class Electrolyte(Component):
    formula: str
    position: PositiveInt
    amount: NonNegativeFloat


class ElectrodeWeight(BaseModel):
    total: NonNegativeFloat
    collector: NonNegativeFloat
    net: Optional[NonNegativeFloat]
    units: Literal["mg", "g"] = "mg"


class Electrode(Component):
    formula: str
    position: PositiveInt
    diameter: Diameter
    weight: ElectrodeWeight
    capacity: Capacity


class Separator(Component):
    name: str  # ? use `Literal` of available?
    diameter: Diameter


class Spacer(Component):
    value: NonNegativeFloat
    units: Literal["mm"] = "mm"


class Composition(BaseModel):
    description: Optional[str]
    anode: Electrode
    cathode: Electrode
    electrolyte: Electrolyte
    separator: Separator
    spacer: Spacer


class BatterySpecs(BaseModel):
    case: str  # ? use `Literal` of available?
    manufacturer: str  # ? use `Literal` of available?
    composition: Composition
    capacity: Capacity
    np_ratio: Optional[str]


class BatteryMetadata(BaseModel):
    name: str
    groups: Set[str] = {"all-samples"}
    batch: str = ""
    subbatch: str = "0"
    creation_datetime: datetime
    creation_process: str


class ChargeState(Flag):
    CHARGED = True
    DISCHARGED = False


class BatteryState(BaseModel):
    used = False
    charged: ChargeState = ChargeState.CHARGED


class BatterySample(BaseModel):
    id: int
    # state: BatteryState  # TODO move to metadata?
    specs: BatterySpecs
    metadata: BatteryMetadata


BatterySpecsJsonTypes = extract_schema_types(BatterySpecs)
BatterySampleJsonTypes = extract_schema_types(BatterySample)
