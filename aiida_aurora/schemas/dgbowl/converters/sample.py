# -*- coding: utf-8 -*-

from aiida_aurora.schemas.battery import BatterySample
from pydantic import BaseModel


def batterysample_to_sample_0(
    batsample: BatterySample,
    SampleSchema: BaseModel):
    """
    Convert a BatterySample into a Sample.

    Compatible with the following dgbowl-schemas payload versions:
        [0.1, 0.2]
    """
    _COMPATIBLE_PAYLOAD_VERSIONS = ["0.1", "0.2"]

    if not isinstance(batsample, BatterySample):
        if isinstance(batsample, dict):
            batsample = BatterySample(**batsample)
        else:
            raise TypeError()
    # if batsample.capacity.units == "mAh":
        # capacity = float(batsample.capacity.nominal) * 0.001
    # elif batsample.capacity.units == "Ah":
        # capacity = float(batsample.capacity.nominal)

    sample = SampleSchema(
        name = batsample.metadata.name,
        capacity = batsample.capacity.nominal
    )
    return sample
