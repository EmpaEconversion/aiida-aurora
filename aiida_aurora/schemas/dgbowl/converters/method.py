from pydantic import BaseModel

from aiida_aurora.schemas.cycling import ElectroChemSequence


def electrochemsequence_to_method_list_0(elchemsequence: ElectroChemSequence, MethodSchema: BaseModel):
    """
    Convert an ElectroChemSequence into a list of Method.
    Parameter values that are None will be ignored.

    Compatible with the following dgbowl-schemas payload versions:
        [0.1, 0.2]
    """

    if not isinstance(elchemsequence, ElectroChemSequence):
        if isinstance(elchemsequence, dict):
            elchemsequence = ElectroChemSequence(**elchemsequence)
        else:
            raise TypeError()
    sequence = []
    for step in elchemsequence.method:
        parameters = {name: param.value for name, param in step.parameters.items() if param.value is not None}

        sequence.append(MethodSchema(**{
            'device': step.device,
            'technique': step.technique,
        }, **parameters))

    return sequence
