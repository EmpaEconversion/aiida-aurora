from __future__ import annotations

import numpy as np

from .parsers import get_data_from_raw


class Analyzer:
    """Base class for all analyzers."""

    def analyze(self, snapshot: dict) -> None:
        """Analyze the experiment snapshot against a condition.

        Condition is defined in subclass analyzers.

        Parameters
        ----------
        `snapshot` : `dict`
            The loaded snapshot dictionary.
        """
        raise NotImplementedError


class CapacityAnalyzer(Analyzer):
    """A battery capacity analyzer.

    Attributes
    ==========
    `check_type` : `str`
        The half-cycle to analyze (charge/discharge),
        `"discharge_capacity"` by default.
    `threshold` : `float`
        The capacity threshold in percent, `0.8` by default.
    `consecutive_cycles` : `int`
        The number of required below-threshold consecutive cycles,
        `2` by default
    """

    def __init__(
        self,
        check_type="discharge_capacity",
        threshold=0.8,
        consecutive_cycles=2,
        keep_last=10,
    ) -> None:
        """`CapacityAnalyzer` constructor.

        Parameters
        ----------
        `check_type` : `str`
            The half-cycle to analyze,
            `"discharge_capacity"` by default.
        `threshold` : `float`
            The capacity threshold in percent, `0.8` by default.
        `consecutive_cycles` : `int`
            The number of required consecutive cycles,
            `2` by default.
        `keep_last` : `int`
            The number of cycles to keep in snapshot.

        Raises
        ------
        `TypeError`
            If `check_type` is not supported.
        """

        if check_type not in {"discharge_capacity", "charge_capacity"}:
            raise TypeError(f"{check_type=} not supported")

        self.threshold = threshold
        self.consecutive = consecutive_cycles
        self.is_discharge = check_type == "discharge_capacity"
        self.keep_last = keep_last

        self.flag = ""
        self.status = ""
        self.report = ""

    def analyze(self, snapshot: dict) -> None:
        """Analyze the snapshot.

        Check if capacity has fallen below threshold for required
        consecutive cycles.

        Parameters
        ----------
        `snapshot` : `dict`
            The loaded snapshot dictionary.
        """
        self._extract_capacities(snapshot)
        self._check_capacity()
        self._truncate_snapshot()

    ###########
    # PRIVATE #
    ###########

    def _extract_capacities(self, snapshot: dict) -> None:
        """Post-process the snapshot to extract capacities.

        Parameters
        ----------
        `snapshot` : `dict`
            The loaded snapshot dictionary.
        """
        try:
            self.snapshot = get_data_from_raw(snapshot)
            self.capacities = self.snapshot["Qd"] \
                if self.is_discharge \
                else self.snapshot["Qc"]
        except KeyError as err:
            self.report = f"missing '{str(err)}' in snapshot"
            self.snapshot = {}
            self.capacities = []

    def _check_capacity(self) -> None:
        """Check if capacity has fallen below threshold for required
        consecutive cycles."""

        if (n := len(self.capacities)) < 2:
            self.report = "need at least two complete cycles"
            return

        Qs = self.capacities[0]
        Q = self.capacities[-2]
        Qt = self.threshold * Qs
        C_per = Q / Qs * 100

        self.report = f"cycle #{n} : {Q = :.2f} mAh ({C_per:.1f}%)"
        self.status = f"(cycle #{n} : C @ {C_per:.1f}%)"

        if Q < Qt:
            self.report += f" - {(Qt - Q) / Qt * 100:.1f}% below threshold"

        below_threshold = np.where(self.capacities < Qt)[0] + 1
        consecutively_below = self._filter_consecutive(below_threshold)

        if len(consecutively_below):

            cycles_str = str(consecutively_below).replace("'", "")
            self.report += f" - cycles below threshold: {cycles_str}"

            if consecutively_below[-1] == n:
                self.flag = "🔴"
            else:
                self.flag = "🟡"

    def _filter_consecutive(self, cycles: list[int]) -> list[int]:
        """Return cycles below threshold for `x` consecutive cycles.

        Parameters
        ----------
        `cycles` : `list[int]`
            The cycles below threshold.

        Returns
        -------
        `list[int]`
            The cycles below threshold for `x` consecutive cycles.
        """
        return [
            cycle for i, cycle in enumerate(cycles)
            if i >= self.consecutive - 1 and \
            all(cycles[i - j] == cycle - j for j in range(1, self.consecutive))
        ]

    def _truncate_snapshot(self) -> None:
        """Truncate the snapshot to user defined size."""

        truncated = {}

        size = min(self.keep_last, len(self.snapshot["cycle-number"]))

        for key, value in self.snapshot.items():

            if key in ("time", "I", "Ewe", "Q"):
                index = self.snapshot["cycle-index"][-size]
                truncated[key] = value[index:]

            elif key in ("cycle-number", "Qc", "Qd", "Ec", "Ed"):
                truncated[key] = value[-size:]

        self.snapshot = truncated
