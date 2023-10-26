from pydantic import BaseModel

from aiida_aurora.schemas.battery import BatterySample


def batterysample_to_sample_0(
    sample: BatterySample,
    SampleSchema: BaseModel,
) -> BaseModel:
    """
    Convert a BatterySample into a Sample.

    Compatible with the following dgbowl-schemas payload versions:
        [0.1, 0.2]
    """

    if not isinstance(sample, BatterySample):
        if isinstance(sample, dict):
            sample = BatterySample(**sample)
        else:
            raise TypeError()
    C = sample.specs.capacity.nominal
    return SampleSchema(
        name=sample.metadata.name,
        capacity=C if sample.specs.capacity.units == "Ah" else C * 0.001,
    )
