# -*- coding: utf-8 -*-

from pydantic import (BaseModel, Extra, NonNegativeFloat, NonNegativeInt)
from typing import Dict, Generic, Sequence, TypeVar, Literal, Union
from pydantic.generics import GenericModel

DataT = TypeVar('DataT')
class CyclingParameter(GenericModel, Generic[DataT]):
    "Cycling parameter of type DataT"
    label: str  # the label used in a widget
    description: str = ""  # a long description
    units: str = ""  # physical units of this parameter
    value: DataT = None  # the set value
    default_value: DataT = None  # the default value of this parameter
    required: bool = False  # True if parameter is required
    
    class Config:
        validate_assignment = True
        extra = Extra.forbid
    
    # @classmethod
    # def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
        # return f'{params[0].__name__.title()}CyclingParameter'

class CyclingTechnique(BaseModel):
    device: Literal["worker", "MPG2"]  # the device name
    technique: str  # the technique name for tomato
    short_name: str  # short name for the technique
    name: str  # a custom name
    description: str = ""
    parameters: Dict[str, CyclingParameter]
    
    class Config:
        validate_assignment = True
        extra = Extra.forbid

allowed_I_ranges = Literal[
    "keep", "100 pA", "1 nA", "10 nA", "100 nA", "1 uA", "10 uA", "100 uA",
    "1 mA", "10 mA", "100 mA", "1 A", "booster", "auto",
]
allowed_E_ranges = Literal[
    "+-2.5 V", "+-5.0 V", "+-10 V", "auto",
]

class DummySequential(CyclingTechnique, extra=Extra.forbid):
    device: Literal["worker"] = "worker"
    technique: Literal["sequential"] = "sequential"
    short_name: Literal["DUMMY_SEQUENTIAL"] = "DUMMY_SEQUENTIAL"
    name = "Dummy Sequential"
    description = "Dummy worker - sequential numbers"
    parameters: Dict[str, CyclingParameter] = {
        "time": CyclingParameter[NonNegativeFloat](
            label = "Time:",
            units = "s",
            default_value = 100.,
            required = True
        ),
        "delay": CyclingParameter[NonNegativeFloat](
            label = "Delay:",
            units = "s",
            default_value = 1.0,
            required = True,
        )
    }

class DummyRandom(CyclingTechnique, extra=Extra.forbid):
    device: Literal["worker"] = "worker"
    technique: Literal["random"] = "random"
    short_name: Literal["DUMMY_RANDOM"] = "DUMMY_RANDOM"
    name = "Dummy Random"
    description = "Dummy worker - random numbers"
    parameters: Dict[str, CyclingParameter] = {
        "time": CyclingParameter[NonNegativeFloat](
            label = "Time:",
            units = "s",
            default_value = 100.,
            required = True
        ),
        "delay": CyclingParameter[NonNegativeFloat](
            label = "Delay:",
            units = "s",
            default_value = 1.0,
            required = True,
        )
    }

class OpenCircuitVoltage(CyclingTechnique, extra=Extra.forbid):
    device: Literal["MPG2"] = "MPG2"
    technique: Literal["open_circuit_voltage"] = "open_circuit_voltage"
    short_name: Literal["OCV"] = "OCV"
    name = "OCV"
    description = "Open circuit voltage"
    parameters: Dict[str, CyclingParameter] = {
        "time": CyclingParameter[NonNegativeFloat](
            label = "Time:",
            description = "The length of the OCV step",
            units = "s",
            default_value = 0.0,
            required = True,
        ),
        "record_every_dt": CyclingParameter[NonNegativeFloat](
            label = "Record every $dt$:",
            description = "Record a datapoint at prescribed time spacing",
            units = "s",
            default_value = 30.0,
            required = True,
        ),
        "record_every_dE": CyclingParameter[NonNegativeFloat](
            label = "Record every $dE$:",
            description = "Record a datapoint at prescribed voltage spacing",
            units = "V",
            default_value = 0.005,
            required = True,
        ),
        "I_range": CyclingParameter[allowed_I_ranges](
            label = "I range",
            description = "",
            default_value = "1 A",  # TODO: "keep" value does not work - setting to 1 A
            required = True,
        ),
        "E_range": CyclingParameter[allowed_E_ranges](
            label = "E range",
            description = "",
            default_value = "auto",
            required = True,
        ),
    }

class ConstantVoltage(CyclingTechnique, extra=Extra.forbid):
    device: Literal["MPG2"] = "MPG2"
    technique: Literal["constant_voltage"] = "constant_voltage"
    short_name: Literal["CV"] = "CV"
    name = "CV"
    description = "Controlled voltage technique, with optional current and voltage limits"
    parameters: Dict[str, CyclingParameter] = {
        "time": CyclingParameter[NonNegativeFloat](
            label = "Time:",
            description = "Maximum duration of the CV step",
            units = "s",
            default_value = 0.0,
            required = True,
        ),
        "voltage": CyclingParameter[float](
            label = "Step voltage:",
            description = "Voltage of the current step",
            units = "V",
            default_value = 0.0,
            required = True,
        ),
        "record_every_dt": CyclingParameter[NonNegativeFloat](
            label = "Record every $dt$:",
            description = "Record a datapoint at prescribed time spacing",
            units = "s",
            default_value = 30.0,
            required = True,
        ),
        "record_every_dI": CyclingParameter[NonNegativeFloat](
            label = "Record every $dI$:",
            description = "Record a datapoint at prescribed current spacing",
            units = "I",
            default_value = 0.001,
            required = True,
        ),
        "I_range": CyclingParameter[allowed_I_ranges](
            label = "I range",
            description = "Select the current range of the potentiostat",
            default_value = "keep",
            required = True,
        ),
        "E_range": CyclingParameter[allowed_E_ranges](
            label = "E range",
            description = "Select the voltage range of the potentiostat",
            default_value = "auto",
            required = True,
        ),
        "n_cycles": CyclingParameter[NonNegativeInt](
            label = "Number of cycles:",
            description = "Cycle through the current technique N times.",
            default_value = 0,
            required = True,
        ),
        "is_delta": CyclingParameter[bool](
            label = "Δ$V$:",
            description = "Is the step voltage a $\Delta$ from previous step?",
            default_value = False,
            required = True,
        ),
        "exit_on_limit": CyclingParameter[bool](
            label = "Exit when limits reached?",
            description = "Stop the whole experiment when limit is reached?",
            default_value = False,
            required = True,
        ),
        "limit_voltage_max": CyclingParameter[float](
            label = "Maximum voltage:",
            description = "Define the upper limit of voltage for this step",
            units = "V",
            default_value = None
        ),
        "limit_voltage_min": CyclingParameter[float](
            label = "Minimum voltage:",
            description = "Define the lower limit of voltage for this step",
            units = "V",
            default_value = None
        ),
        "limit_current_max": CyclingParameter[Union[float, str]](
            label = "Maximum current:",
            description = "Define the upper limit of current for this step",
            units = "I",
            default_value = None
        ),
        "limit_current_min": CyclingParameter[Union[float, str]](
            label = "Minimum current:",
            description = "Define the lower limit of current for this step",
            units = "I",
            default_value = None
        )
    }

class ConstantCurrent(CyclingTechnique, extra=Extra.forbid):
    device: Literal["MPG2"] = "MPG2"
    technique: Literal["constant_current"] = "constant_current"
    short_name: Literal["CC"] = "CC"
    name = "CC"
    description = "Controlled current technique, with optional voltage and current limits"
    parameters: Dict[str, CyclingParameter] = {
        "time": CyclingParameter[NonNegativeFloat](
            label = "Time:",
            description = "Maximum duration of the CC step",
            units = "s",
            default_value = 0.0,
            required = True,
        ),
        "current": CyclingParameter[Union[float, str]](
            label = "Step current:",
            description = "Current during the current step",
            units = "I",
            default_value = 0.0,
            required = True,
        ),
        "record_every_dt": CyclingParameter[NonNegativeFloat](
            label = "Record every $dt$:",
            description = "Record a datapoint at prescribed time spacing",
            units = "s",
            default_value = 30.0,
            required = True,
        ),
        "record_every_dE": CyclingParameter[NonNegativeFloat](
            label = "Record every $dE$:",
            description = "Record a datapoint at prescribed voltage spacing",
            units = "V",
            default_value = 0.005,
            required = True,
        ),
        "I_range": CyclingParameter[allowed_I_ranges](
            label = "I range",
            description = "Select the current range of the potentiostat",
            default_value = "keep",
            required = True,
        ),
        "E_range": CyclingParameter[allowed_E_ranges](
            label = "E range",
            description = "Select the voltage range of the potentiostat",
            default_value = "auto",
            required = True,
        ),
        "n_cycles": CyclingParameter[NonNegativeInt](
            label = "Number of cycles:",
            description = "Cycle through the current technique N times.",
            default_value = 0,
            required = True,
        ),
        "is_delta": CyclingParameter[bool](
            label = "Δ$I$:",
            description = "Is the step current a $\Delta$ from previous step?",
            default_value = False,
            required = True,
        ),
        "exit_on_limit": CyclingParameter[bool](
            label = "Exit when limits reached?",
            description = "Stop the whole experiment when limit is reached?",
            default_value = False,
            required = True,
        ),
        "limit_voltage_max": CyclingParameter[float](
            label = "Maximum voltage:",
            description = "Define the upper limit of voltage for this step",
            units = "V",
            default_value = None
        ),
        "limit_voltage_min": CyclingParameter[float](
            label = "Minimum voltage:",
            description = "Define the lower limit of voltage for this step",
            units = "V",
            default_value = None
        ),
        "limit_current_max": CyclingParameter[Union[float, str]](
            label = "Maximum current:",
            description = "Define the upper limit of current for this step",
            units = "I",
            default_value = None
        ),
        "limit_current_min": CyclingParameter[Union[float, str]](
            label = "Minimum current:",
            description = "Define the lower limit of current for this step",
            units = "I",
            default_value = None
        )
    }

#class SweepVoltage(CyclingTechnique, extra=Extra.forbid):
#    technique: Literal["sweep_voltage"] = "sweep_voltage"
#    short_name: Literal["LSV"] = "LSV"
#    name = "LSV"
#    description = "Controlled voltage technique, allowing linear change of voltage between pre-defined endpoints as a function of time, with optional current and voltage limits"

#class SweepCurrent(CyclingTechnique, extra=Extra.forbid):
#    technique: Literal["sweep_current"] = "sweep_current"
#    short_name: Literal["LSC"] = "LSC"
#    name = ""
#    description = "Controlled current technique, allowing linear change of current between pre-defined endpoints as a function of time, with optional current and voltage limits"

class Loop(CyclingTechnique, extra=Extra.forbid):
    device: Literal["MPG2"] = "MPG2"
    technique: Literal["loop"] = "loop"
    short_name: Literal["LOOP"] = "LOOP"
    name = "LOOP"
    description = "Loop technique, allowing to repeat a set of preceding techniques in a technique array"
    parameters: Dict[str, CyclingParameter] = {
        "n_gotos": CyclingParameter[int](
            label = "Repeats",
            description = "Number of times the technique will jump; set to -1 for unlimited",
            default_value = -1,
            required = True,
        ),
        "goto": CyclingParameter[int](
            label = "Go to:",
            description = "Index of the technique to go back to",
            default_value = 1,
            required = True,
        ),
    }

ElectroChemPayloads = Union[
    DummySequential,
    DummyRandom,
    OpenCircuitVoltage,
    ConstantCurrent,
    ConstantVoltage,
#    SweepCurrent,
#    SweepVoltage,
    Loop,
]

class ElectroChemSequence(BaseModel):
    method: Sequence[ElectroChemPayloads]
    
    @property
    def n_steps(self):
        "Number of steps of the method"
        return len(self.method)

    def add_step(self, elem):
        if not isinstance(elem, ElectroChemPayloads.__args__):
            raise ValueError("Invalid technique")
        self.method.append(elem)
    
    def remove_step(self, index):
        self.method.pop(index)
    
    def move_step_backward(self, index):
        if index > 0:
            self.method[index-1], self.method[index] = self.method[index], self.method[index-1]

    def move_step_forward(self, index):
        if index < self.n_steps - 1:
            self.method[index], self.method[index+1] = self.method[index+1], self.method[index]
        
    class Config:
        validate_assignment = True
        extra = Extra.forbid