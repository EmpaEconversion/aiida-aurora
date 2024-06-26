"""
STATUS: Providing the parameters as a dict with the specific parameter dict
as a default is not allowing me to initialize the CyclingTechnique's with
a normal dictionary (the parameters dict is not being correctly converted
to the right type but to t.[DataT] I think).

Using TypedDict as suggested here is not working properly either:
https://stackoverflow.com/q/74643755/638366

I probably need to change something fundamentally with how the CyclingTechnique
and CyclingParameter interact with each other but I'm not sure what currently,
so for now I'm defining the InternalParameters as its own class inside each of
the CyclingTechnique's.

I also need to add items and __getitem__ because some other parts of the code
expect it to behave like a dict...
"""

import typing as t

from pydantic import BaseModel, ConfigDict, NonNegativeFloat, NonNegativeInt

DataT = t.TypeVar("DataT")


class CyclingParameter(BaseModel, t.Generic[DataT]):
    "Cycling parameter of type DataT"

    label: str  # the label used in a widget
    description: str = ""  # a long description
    units: str = ""  # physical units of this parameter
    value: t.Optional[DataT] = None  # the set value
    default_value: t.Optional[DataT] = None  # the default value
    required: bool = False  # True if parameter is required
    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # @classmethod
    # def __concrete_name__(cls: Type[Any], params: Tuple[Type[Any], ...]) -> str:
    # return f'{params[0].__name__.title()}CyclingParameter'


class CyclingTechnique(BaseModel):
    device: t.Literal["worker", "MPG2"]  # the device name
    technique: str  # the technique name for tomato
    short_name: str  # short name for the technique
    name: str  # a custom name
    description: str = ""
    parameters: t.Dict[str, CyclingParameter]
    model_config = ConfigDict(validate_assignment=True, extra="forbid")


allowed_I_ranges = t.Literal["keep",
                             "100 pA",
                             "1 nA",
                             "10 nA",
                             "100 nA",
                             "1 uA",
                             "10 uA",
                             "100 uA",
                             "1 mA",
                             "10 mA",
                             "100 mA",
                             "1 A",
                             "booster",
                             "auto",
                             ]
allowed_E_ranges = t.Literal["+-2.5 V", "+-5.0 V", "+-10 V", "auto",]

################################################################################
# SPECIFIC TECHNIQUES
################################################################################


class DummySequential(CyclingTechnique):
    device: t.Literal["worker"] = "worker"
    technique: t.Literal["sequential"] = "sequential"
    short_name: t.Literal["DUMMY_SEQUENTIAL"] = "DUMMY_SEQUENTIAL"
    name: str = "Dummy Sequential"
    description: str = "Dummy worker - sequential numbers"

    class InternalParameters(BaseModel):
        time: CyclingParameter[NonNegativeFloat]
        delay: CyclingParameter[NonNegativeFloat]

        @property
        def items(self):
            return dict(iter(self)).items

        def __getitem__(self, item):
            return getattr(self, item)

    # parameters: t.Dict[str, CyclingParameter] = {
    parameters: InternalParameters = InternalParameters(
        **{
            "time": CyclingParameter[NonNegativeFloat](
                label="Time:",
                units="s",
                default_value=100.0,
                required=True,
            ),
            "delay": CyclingParameter[NonNegativeFloat](
                label="Delay:",
                units="s",
                default_value=1.0,
                required=True,
            ),
        }
    )


################################################################################
class DummyRandom(CyclingTechnique):
    device: t.Literal["worker"] = "worker"
    technique: t.Literal["random"] = "random"
    short_name: t.Literal["DUMMY_RANDOM"] = "DUMMY_RANDOM"
    name: str = "Dummy Random"
    description: str = "Dummy worker - random numbers"

    class InternalParameters(BaseModel):
        time: CyclingParameter[NonNegativeFloat]
        delay: CyclingParameter[NonNegativeFloat]

        @property
        def items(self):
            return dict(iter(self)).items

        def __getitem__(self, item):
            return getattr(self, item)

    # parameters: t.Dict[str, CyclingParameter] = {
    parameters: InternalParameters = InternalParameters(
        **{
            "time": CyclingParameter[NonNegativeFloat](
                label="Time:",
                units="s",
                default_value=100.0,
                required=True,
            ),
            "delay": CyclingParameter[NonNegativeFloat](
                label="Delay:",
                units="s",
                default_value=1.0,
                required=True,
            ),
        }
    )


################################################################################
class OpenCircuitVoltage(CyclingTechnique):
    device: t.Literal["MPG2"] = "MPG2"
    technique: t.Literal["open_circuit_voltage"] = "open_circuit_voltage"
    short_name: t.Literal["OCV"] = "OCV"
    name: str = "OCV"
    description: str = "Open circuit voltage"

    class InternalParameters(BaseModel):
        time: CyclingParameter[NonNegativeFloat]
        record_every_dt: CyclingParameter[NonNegativeFloat]
        record_every_dE: CyclingParameter[NonNegativeFloat]
        I_range: CyclingParameter[allowed_I_ranges]
        E_range: CyclingParameter[allowed_E_ranges]

        @property
        def items(self):
            return dict(iter(self)).items

        def __getitem__(self, item):
            return getattr(self, item)

    # parameters: t.Dict[str, CyclingParameter] = {
    parameters: InternalParameters = InternalParameters(
        **{
            "time":
            CyclingParameter[NonNegativeFloat](
                label="Time:",
                description="The length of the OCV step",
                units="s",
                default_value=0.0,
                required=True,
            ),
            "record_every_dt":
            CyclingParameter[NonNegativeFloat](
                label="Record every $dt$:",
                description="Record a datapoint at prescribed time spacing",
                units="s",
                default_value=30.0,
                required=True,
            ),
            "record_every_dE":
            CyclingParameter[NonNegativeFloat](
                label="Record every $dE$:",
                description="Record a datapoint at prescribed voltage spacing",
                units="V",
                default_value=0.005,
                required=True,
            ),
            "I_range":
            CyclingParameter[allowed_I_ranges](
                label="I range",
                description="",
                # TODO: "keep" value does not work - setting to 1 A
                default_value="1 A",
                required=True,
            ),
            "E_range":
            CyclingParameter[allowed_E_ranges](
                label="E range",
                description="",
                default_value="auto",
                required=True,
            ),
        }
    )


################################################################################
class ConstantVoltage(CyclingTechnique):
    device: t.Literal["MPG2"] = "MPG2"
    technique: t.Literal["constant_voltage"] = "constant_voltage"
    short_name: t.Literal["CV"] = "CV"
    name: str = "CV"
    description: str = ("Controlled voltage technique, with optional current and voltage limits")

    class InternalParameters(BaseModel):
        time: CyclingParameter[NonNegativeFloat]
        voltage: CyclingParameter[float]
        record_every_dt: CyclingParameter[NonNegativeFloat]
        record_every_dI: CyclingParameter[NonNegativeFloat]
        I_range: CyclingParameter[allowed_I_ranges]
        E_range: CyclingParameter[allowed_E_ranges]
        n_cycles: CyclingParameter[NonNegativeInt]
        is_delta: CyclingParameter[bool]
        exit_on_limit: CyclingParameter[bool]
        limit_voltage_max: CyclingParameter[float]
        limit_voltage_min: CyclingParameter[float]
        limit_current_max: CyclingParameter[t.Union[float, str]]
        limit_current_min: CyclingParameter[t.Union[float, str]]

        @property
        def items(self):
            return dict(iter(self)).items

        def __getitem__(self, item):
            return getattr(self, item)

    # parameters: t.Dict[str, CyclingParameter] = {
    parameters: InternalParameters = InternalParameters(
        **{
            "time":
            CyclingParameter[NonNegativeFloat](
                label="Time:",
                description="Maximum duration of the CV step",
                units="s",
                default_value=0.0,
                required=True,
            ),
            "voltage":
            CyclingParameter[float](
                label="Step voltage:",
                description="Voltage of the current step",
                units="V",
                default_value=0.0,
                required=True,
            ),
            "record_every_dt":
            CyclingParameter[NonNegativeFloat](
                label="Record every $dt$:",
                description="Record a datapoint at prescribed time spacing",
                units="s",
                default_value=30.0,
                required=True,
            ),
            "record_every_dI":
            CyclingParameter[NonNegativeFloat](
                label="Record every $dI$:",
                description="Record a datapoint at prescribed current spacing",
                units="I",
                default_value=0.001,
                required=True,
            ),
            "I_range":
            CyclingParameter[allowed_I_ranges](
                label="I range",
                description="Select the current range of the potentiostat",
                default_value="keep",
                required=True,
            ),
            "E_range":
            CyclingParameter[allowed_E_ranges](
                label="E range",
                description="Select the voltage range of the potentiostat",
                default_value="auto",
                required=True,
            ),
            "n_cycles":
            CyclingParameter[NonNegativeInt](
                label="Number of cycles:",
                description="Cycle through the current technique N times.",
                default_value=0,
                required=True,
            ),
            "is_delta":
            CyclingParameter[bool](
                label="Δ$V$:",
                description=r"""
                    Is the step voltage a $\Delta$ from previous step?
                """,
                default_value=False,
                required=True,
            ),
            "exit_on_limit":
            CyclingParameter[bool](
                label="Exit when limits reached?",
                description="Stop the whole experiment when limit is reached?",
                default_value=False,
                required=True,
            ),
            "limit_voltage_max":
            CyclingParameter[float](
                label="Maximum voltage:",
                description="Define the upper limit of voltage for this step",
                units="V",
                default_value=None,
            ),
            "limit_voltage_min":
            CyclingParameter[float](
                label="Minimum voltage:",
                description="Define the lower limit of voltage for this step",
                units="V",
                default_value=None,
            ),
            "limit_current_max":
            CyclingParameter[t.Union[float, str]](
                label="Maximum current:",
                description="Define the upper limit of current for this step",
                units="I",
                default_value=None,
            ),
            "limit_current_min":
            CyclingParameter[t.Union[float, str]](
                label="Minimum current:",
                description="Define the lower limit of current for this step",
                units="I",
                default_value=None,
            ),
        }
    )


################################################################################
class ConstantCurrent(CyclingTechnique):
    device: t.Literal["MPG2"] = "MPG2"
    technique: t.Literal["constant_current"] = "constant_current"
    short_name: t.Literal["CC"] = "CC"
    name: str = "CC"
    description: str = ("Controlled current technique, with optional voltage and current limits")

    class InternalParameters(BaseModel):
        time: CyclingParameter[NonNegativeFloat]
        current: CyclingParameter[t.Union[float, str]]
        record_every_dt: CyclingParameter[NonNegativeFloat]
        record_every_dE: CyclingParameter[NonNegativeFloat]
        I_range: CyclingParameter[allowed_I_ranges]
        E_range: CyclingParameter[allowed_E_ranges]
        n_cycles: CyclingParameter[NonNegativeInt]
        is_delta: CyclingParameter[bool]
        exit_on_limit: CyclingParameter[bool]
        limit_voltage_max: CyclingParameter[float]
        limit_voltage_min: CyclingParameter[float]
        limit_current_max: CyclingParameter[t.Union[float, str]]
        limit_current_min: CyclingParameter[t.Union[float, str]]

        @property
        def items(self):
            return dict(iter(self)).items

        def __getitem__(self, item):
            return getattr(self, item)

    # parameters: t.Dict[str, CyclingParameter] = {
    parameters: InternalParameters = InternalParameters(
        **{
            "time":
            CyclingParameter[NonNegativeFloat](
                label="Time:",
                description="Maximum duration of the CC step",
                units="s",
                default_value=0.0,
                required=True,
            ),
            "current":
            CyclingParameter[t.Union[float, str]](
                label="Step current:",
                description="Current during the current step",
                units="I",
                default_value=0.0,
                required=True,
            ),
            "record_every_dt":
            CyclingParameter[NonNegativeFloat](
                label="Record every $dt$:",
                description="Record a datapoint at prescribed time spacing",
                units="s",
                default_value=30.0,
                required=True,
            ),
            "record_every_dE":
            CyclingParameter[NonNegativeFloat](
                label="Record every $dE$:",
                description="Record a datapoint at prescribed voltage spacing",
                units="V",
                default_value=0.005,
                required=True,
            ),
            "I_range":
            CyclingParameter[allowed_I_ranges](
                label="I range",
                description="Select the current range of the potentiostat",
                default_value="keep",
                required=True,
            ),
            "E_range":
            CyclingParameter[allowed_E_ranges](
                label="E range",
                description="Select the voltage range of the potentiostat",
                default_value="auto",
                required=True,
            ),
            "n_cycles":
            CyclingParameter[NonNegativeInt](
                label="Number of cycles:",
                description="Cycle through the current technique N times.",
                default_value=0,
                required=True,
            ),
            "is_delta":
            CyclingParameter[bool](
                label="Δ$I$:",
                description=r"""
                    Is the step current a $\Delta$ from previous step?
                """,
                default_value=False,
                required=True,
            ),
            "exit_on_limit":
            CyclingParameter[bool](
                label="Exit when limits reached?",
                description="Stop the whole experiment when limit is reached?",
                default_value=False,
                required=True,
            ),
            "limit_voltage_max":
            CyclingParameter[float](
                label="Maximum voltage:",
                description="Define the upper limit of voltage for this step",
                units="V",
                default_value=None,
            ),
            "limit_voltage_min":
            CyclingParameter[float](
                label="Minimum voltage:",
                description="Define the lower limit of voltage for this step",
                units="V",
                default_value=None,
            ),
            "limit_current_max":
            CyclingParameter[t.Union[float, str]](
                label="Maximum current:",
                description="Define the upper limit of current for this step",
                units="I",
                default_value=None,
            ),
            "limit_current_min":
            CyclingParameter[t.Union[float, str]](
                label="Minimum current:",
                description="Define the lower limit of current for this step",
                units="I",
                default_value=None,
            ),
        }
    )


################################################################################
# class SweepVoltage(CyclingTechnique):
#    technique: t.Literal["sweep_voltage"] = "sweep_voltage"
#    short_name: t.Literal["LSV"] = "LSV"
#    name: str = "LSV"
#    description: str = "Controlled voltage technique, allowing linear change of voltage between pre-defined endpoints as a function of time, with optional current and voltage limits"

################################################################################
# class SweepCurrent(CyclingTechnique):
#    technique: t.Literal["sweep_current"] = "sweep_current"
#    short_name: t.Literal["LSC"] = "LSC"
#    name: str = ""
#    description: str = "Controlled current technique, allowing linear change of current between pre-defined endpoints as a function of time, with optional current and voltage limits"


################################################################################
class Loop(CyclingTechnique):
    device: t.Literal["MPG2"] = "MPG2"
    technique: t.Literal["loop"] = "loop"
    short_name: t.Literal["LOOP"] = "LOOP"
    name: str = "LOOP"
    description: str = "Loop technique, allowing to repeat a set of preceding techniques in a technique array"

    class InternalParameters(BaseModel):
        n_gotos: CyclingParameter[int]
        goto: CyclingParameter[int]

        @property
        def items(self):
            return dict(iter(self)).items

        def __getitem__(self, item):
            return getattr(self, item)

    # parameters: t.Dict[str, CyclingParameter] = {
    parameters: InternalParameters = InternalParameters(
        **{
            "n_gotos":
            CyclingParameter[int](
                label="Repeats",
                description="Number of times the technique will jump; set to -1 for unlimited",
                default_value=-1,
                required=True,
            ),
            "goto":
            CyclingParameter[int](
                label="Go to:",
                description="Index of the technique to go back to",
                default_value=1,
                required=True,
            ),
        }
    )


################################################################################
# SEQUENCE OF TECHNIQUES
################################################################################

ElectroChemPayloads = t.Union[DummySequential,
                              DummyRandom,
                              OpenCircuitVoltage,
                              ConstantCurrent,
                              ConstantVoltage,
                              #    SweepCurrent,
                              #    SweepVoltage,
                              Loop,
                              ]


class ElectroChemSequence(BaseModel):
    name: str = ""
    method: t.Sequence[ElectroChemPayloads]
    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    @property
    def n_steps(self):
        "Number of steps of the method"
        return len(self.method)

    def set_name(self, name: str) -> None:
        """docstring"""
        self.name = name

    def add_step(self, elem):
        if not isinstance(elem, t.get_args(ElectroChemPayloads)):
            raise ValueError("Invalid technique")
        self.method.append(elem)

    def remove_step(self, index):
        self.method.pop(index)

    def move_step_backward(self, i):
        if i > 0:
            j = i - 1
            self.method[j], self.method[i] = self.method[i], self.method[j]

    def move_step_forward(self, i):
        if i < self.n_steps - 1:
            j = i + 1
            self.method[i], self.method[j] = self.method[j], self.method[i]
