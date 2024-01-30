import numpy as np
from scipy.integrate import cumtrapz

from aiida.orm import ArrayData


def get_data_from_raw(jsdata: dict) -> dict:
    """Extract raw data from json file.

    Parameters
    ----------
    `jsdata` : `dict`
        The raw JSON data.

    Returns
    -------
    `dict`
        The post-processed data.

    Raises
    ------
    `TypeError`
        If `jsdata` is not a dictionary.
    `NotImplementedError`
        If `jsdata` contains more than one step.
    """

    if not isinstance(jsdata, dict):
        raise TypeError("jsdata should be a dictionary")

    if len(jsdata["steps"]) > 1:
        raise NotImplementedError("multi-step analysis not implemented.")

    raw_data = jsdata["steps"][0]["data"]

    # extract raw data
    t = np.array([ts["uts"] for ts in raw_data]) - raw_data[0]["uts"]
    Ewe = np.array([ts["raw"]["Ewe"]["n"] for ts in raw_data])
    I = np.array([ts["raw"]["I"]["n"] for ts in raw_data])

    return post_process_data(t, Ewe, I)


def get_data_from_results(array_node: ArrayData) -> dict:
    """Extract data from parsed ArrayData node.

    Parameters
    ----------
    `array_node` : `ArrayData`
        The cycling experiment results node.

    Returns
    -------
    `dict`
        The post-processed data.

    Raises
    ------
    `TypeError`
        If `array_node` is not an `ArrayData` node.
    """

    if not isinstance(array_node, ArrayData):
        raise TypeError("array_node should be an ArrayData")

    # collect data
    t = array_node.get_array("step0_uts")
    t -= t[0]
    Ewe = array_node.get_array("step0_Ewe_n")
    I = array_node.get_array("step0_I_n")

    return post_process_data(t, Ewe, I)


def post_process_data(t: np.ndarray, Ewe: np.ndarray, I: np.ndarray) -> dict:
    """Post-process raw data.

    Processes:
    - Determine half-cycle markers
    - Integrate continuous charge
    - Collect charge/discharge capacities
    -

    Parameters
    ----------
    `t` : `np.ndarray`
        The raw time data [s].
    `Ewe` : `np.ndarray`
        The raw voltage data [V].
    `I` : `np.ndarray`
        The raw current data [A].

    Returns
    -------
    `dict`
        The post-processed data.
    """

    mask = I != 0  # filter out zero current
    t, Ewe, I = t[mask], Ewe[mask], I[mask]

    # mark half-cycles (including first and last values)
    idx = np.where(np.diff(np.sign(I), prepend=0) != 0)[0]
    idx = np.append(idx, len(I))

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
        "time": t,
        "Ewe": Ewe,
        "I": I,
        "cycle-number": np.arange(len(Qd)),
        "time-cycles": t[idx[2::2]],
        "Q": cumtrapz(I, t, axis=0, initial=0) / 3.6,
        "Qd": np.array(Qd) / 3.6,
        "Qc": np.array(Qc) / 3.6,
    }
