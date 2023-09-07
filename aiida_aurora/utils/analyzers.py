from itertools import groupby
from logging import LoggerAdapter
from typing import Optional

from aiida.common.log import AIIDA_LOGGER, LOG_LEVEL_REPORT

from .parsers import get_data_from_raw


class Analyzer:
    """Base class for all analyzers.

    Attributes
    ==========
    `logger` : `Union[AiidaLoggerType, LoggerAdapter]`
        The associated logger.
    """

    logger = AIIDA_LOGGER.getChild("monitor")

    def set_logger(self, logger: LoggerAdapter) -> None:
        """Set the analyzer logger.

        Parameters
        ----------
        `logger` : `LoggerAdapter`
            The logger of the analyzed calculation node.
        """
        self.logger = logger

    def analyze(self, snapshot: dict) -> Optional[str]:
        """Analyze the experiment snapshot against a condition.

        Condition is defined in subclass analyzers.

        Parameters
        ----------
        `snapshot` : `dict`
            The loaded snapshot dictionary.

        Returns
        -------
        `Optional[str]`
            A string if a defined condition has been met,
            `None` otherwise.
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

    def analyze(self, snapshot: dict) -> Optional[str]:
        """Analyze the snapshot.

        Check if capacity has fallen below threshold for required
        consecutive cycles.

        Parameters
        ----------
        `snapshot` : `dict`
            The loaded snapshot dictionary.

        Returns
        -------
        `Optional[str]`
            If condition is met, an exit message, `None` otherwise.
        """
        self.capacities = self._get_capacities(snapshot)
        self.cycles = len(self.capacities)
        return None if self.cycles < 1 else self._check_capacity()

    ###########
    # PRIVATE #
    ###########

    def _get_capacities(self, snapshot: dict):
        """Post-process the snapshot to extract capacities.

        Parameters
        ----------
        `snapshot` : `dict`
            The loaded snapshot dictionary.

        Returns
        -------
        `_type_`
            A `numpy` array of capacities (in mAh), or empty list
            if failed to process snapshot.
        """
        try:
            data = get_data_from_raw(snapshot)
            capacities = data['Qd'] if self.is_discharge else data['Qc']
            return capacities / 3.6  # As -> mAh
        except KeyError as err:
            self.logger.error(f"missing '{str(err)}' in snapshot")
        return []

    def _check_capacity(self) -> Optional[str]:
        """Check if capacity has fallen below threshold for required
        consecutive cycles.

        Returns
        -------
        `Optional[str]`
            If condition is met, an exit message, `None` otherwise.
        """

        n = self.cycles
        Qs = self.capacities[0]
        Q = self.capacities[-1]
        Qt = self.threshold * Qs

        message = f"cycle #{n} : {Q = :.2f} mAh ({Q / Qs * 100:.1f}%)"

        if Q < Qt:
            message += f" : {(Qt - Q) / Qt * 100:.1f}% below threshold"

        self.logger.log(LOG_LEVEL_REPORT, message)

        below_threshold = self._count_cycles_below_threshold()
        if below_threshold >= self.consecutive:
            return f"Capacity below threshold ({Qt:.2f} mAh) " \
                   f"for {below_threshold} cycles!"

        return None

    def _count_cycles_below_threshold(self) -> int:
        """Count the number of consecutive cycles below threshold.

        Returns
        -------
        `int`
            The number of consecutive cycles below threshold.
        """
        Qt = self.threshold * self.capacities[0]
        return next(
            (
                len(list(group))  # cycle-count of first below-threshold group
                for below, group in groupby(self.capacities < Qt)
                if below
            ),
            0,
        )
