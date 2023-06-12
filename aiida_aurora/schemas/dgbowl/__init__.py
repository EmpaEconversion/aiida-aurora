"""
Tools to convert aurora schemas to dgbowl-schemas
"""

from dgbowl_schemas.tomato.payload_0_1 import Payload as Payload_0p1
from dgbowl_schemas.tomato.payload_0_1.method import Method as Method_0p1
from dgbowl_schemas.tomato.payload_0_1.sample import Sample as Sample_0p1
from dgbowl_schemas.tomato.payload_0_1.tomato import Tomato as Tomato_0p1
from dgbowl_schemas.tomato.payload_0_2 import Payload as Payload_0p2
from dgbowl_schemas.tomato.payload_0_2.method import Method as Method_0p2
from dgbowl_schemas.tomato.payload_0_2.sample import Sample as Sample_0p2
from dgbowl_schemas.tomato.payload_0_2.tomato import Tomato as Tomato_0p2

from .converters.method import electrochemsequence_to_method_list_0
from .converters.sample import batterysample_to_sample_0

payload_models = {
    "0.2": Payload_0p2,
    "0.1": Payload_0p1,
}

conversion_map = {
    "0.1": {
        "method": lambda obj: electrochemsequence_to_method_list_0(obj, Method_0p1),
        "sample": lambda obj: batterysample_to_sample_0(obj, Sample_0p1),
        "tomato": Tomato_0p1,
    },
    "0.2": {
        "method": lambda obj: electrochemsequence_to_method_list_0(obj, Method_0p2),
        "sample": lambda obj: batterysample_to_sample_0(obj, Sample_0p2),
        "tomato": Tomato_0p2,
    },
}
