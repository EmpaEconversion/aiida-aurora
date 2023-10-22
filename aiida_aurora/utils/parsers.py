import numpy as np
from scipy.integrate import cumtrapz

from aiida.orm import ArrayData


def get_data_from_raw(jsdata) -> dict:
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

    return post_process_data(t, Ewe, I)


def get_data_from_results(array_node) -> dict:
    "Extract data from parsed ArrayData node."

    if not isinstance(array_node, ArrayData):
        raise TypeError('array_node should be an ArrayData')

    # collect data
    t = array_node.get_array('step0_uts')
    t -= t[0]
    Ewe = array_node.get_array('step0_Ewe_n')
    I = array_node.get_array('step0_I_n')

    return post_process_data(t, Ewe, I)


def post_process_data(t: np.ndarray, Ewe: np.ndarray, I: np.ndarray) -> dict:
    """docstring"""

    # find half-cycle markers
    # add last point if not already a marker
    idx = np.where(np.diff(np.sign(I)) != 0)[0]
    if (final := len(I) - 1) not in idx:
        idx = np.append(idx, final)

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
        'Qd': np.array(Qd) / 3.6,
        'Qc': np.array(Qc) / 3.6,
    }
