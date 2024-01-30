from __future__ import annotations

from json import load
from tempfile import NamedTemporaryFile

from aiida.common.log import LOG_LEVEL_REPORT
from aiida.orm import CalcJobNode
from aiida.transports import Transport

from .utils.analyzers import CapacityAnalyzer


def monitor_capacity_threshold(
    node: CalcJobNode,
    transport: Transport,
    settings: dict,
    filename="snapshot.json",
) -> str | None:
    """Retrieve and inspect snapshot to determine if capacity has
    fallen below threshold for several consecutive cycles.

    Parameters
    ----------
    `node` : `CalcJobNode`
        The calculation node.
    `transport` : `Transport`
        The associated transport instance.
    `settings` : `dict`
        The monitor settings.
    `filename` : `str`
        The polled source file, `"snapshot.json"` by default.

    Returns
    -------
    `Optional[str]`
        If condition is met, an exit message, `None` otherwise.

    Raises
    ------
    `TypeError`
        If source file is not in expected dictionary format (JSON).
    `ValueError`
        If source file is empty.
    `FileNotFoundError`
        If the file does not exist in the working directory.
    `OSError`
        If another error occurred while reading the file.
    `Exception`
        If something else prevented analysis.
    """

    analyzer = CapacityAnalyzer(**settings)

    try:

        with transport:

            remote_path = f"{node.get_remote_workdir()}/{filename}"

            if not transport.isfile(remote_path):
                node.logger.info(f"'{filename}' not yet produced; continue")
                return None

            try:

                with NamedTemporaryFile("w+") as temp_file:
                    transport.getfile(remote_path, temp_file.name)
                    snapshot = load(temp_file)

                if not isinstance(snapshot, dict):
                    raise TypeError

                if not snapshot:
                    raise ValueError

                analyzer.analyze(snapshot)

                node.base.extras.set_many({
                    "status": analyzer.status,
                    "snapshot": analyzer.snapshot,
                })

                node.logger.log(LOG_LEVEL_REPORT, analyzer.report)

                if node.base.extras.get("marked_for_death", False):

                    node.base.extras.set("flag", "☠️")

                    if "snapshot" in node.base.extras:
                        node.base.extras.delete("snapshot")

                    return "Job terminated by monitor per user request"

                if analyzer.flag:
                    node.base.extras.set("flag", f"🍅{analyzer.flag}")

            except TypeError:
                node.logger.error(f"'{filename}' not in dictionary format")
            except ValueError:
                node.logger.error(f"'{filename}' is empty")
            except FileNotFoundError:
                node.logger.error(f"error fetching '{filename}'")
            except OSError as err:
                node.logger.error(str(err))

            return None

    except Exception as err:
        node.logger.error(str(err))
        return None
