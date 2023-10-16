import numpy as np

from aiida.orm import ArrayData


def get_data_from_raw(jsdata):
    "Extract raw data from json file."
    if not isinstance(jsdata, dict):
        raise TypeError('jsdata should be a dictionary')
    if len(jsdata["steps"]) > 1:
        raise NotImplementedError('Analysis of multiple steps is not implemented.')

    raw_data = jsdata["steps"][0]["data"]

    # extract raw data
    t = np.array([ts["uts"] for ts in raw_data]) - raw_data[0]["uts"]
    Ewe = np.array([ts["raw"]["Ewe"]["n"] for ts in raw_data])
    I = np.array([ts["raw"]["I"]["n"] for ts in raw_data])

    # find indices of sign changes in I
    idx = np.where(np.diff(np.sign(I)) != 0)[0]

    # integrate and store charge and discharge currents
    Qc, Qd = [], []
    for ii in range(len(idx) - 1):
        i0, ie = idx[ii], idx[ii + 1]
        if ie - i0 < 10:
            continue
        q = np.trapz(I[i0:ie], t[i0:ie])
        if q > 0:
            Qc.append(q)
        else:
            Qd.append(abs(q))

    return {
        'time': t,
        'Ewe': Ewe,
        'I': I,
        'cn': len(Qd),
        'time-cycles': t[idx[2::2]],
        'Qd': np.array(Qd),
        'Qc': np.array(Qc),
    }


def get_data_from_results(array_node):
    "Extract data from parsed ArrayData node."
    if not isinstance(array_node, ArrayData):
        raise TypeError('array_node should be an ArrayData')

    # collect data
    t = array_node.get_array('step0_uts')
    t -= t[0]
    Ewe = array_node.get_array('step0_Ewe_n')
    I = array_node.get_array('step0_I_n')

    # find indices of sign changes in I
    idx = np.where(np.diff(np.sign(I)) != 0)[0]

    # integrate and store charge and discharge currents
    Qc, Qd = [], []
    for ii in range(len(idx) - 1):
        i0, ie = idx[ii], idx[ii + 1]
        if ie - i0 < 10:
            continue
        q = np.trapz(I[i0:ie], t[i0:ie])
        if q > 0:
            Qc.append(q)
        else:
            Qd.append(abs(q))

    return {
        'time': t,
        'Ewe': Ewe,
        'I': I,
        'cn': len(Qd),
        'time-cycles': t[idx[2::2]],
        'Qd': np.array(Qd),
        'Qc': np.array(Qc),
    }
