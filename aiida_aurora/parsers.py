"""
Parsers provided by aiida_aurora.

Register parsers via the "aiida.parsers" entry point in setup.json.
"""
import json
import os
import re

import numpy as np

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import ArrayData, SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

BatteryCyclerExperiment = CalculationFactory("aurora.cycler")


class TomatoParser(Parser):
    """
    Parser class for parsing output of calculation.
    """

    def __init__(self, node):
        """
        Initialize Parser instance

        Checks that the ProcessNode being passed was produced by a DiffCalculation.

        :param node: ProcessNode of calculation
        :param type node: :class:`aiida.orm.ProcessNode`
        """
        super().__init__(node)
        if not issubclass(node.process_class, BatteryCyclerExperiment):
            raise exceptions.ParsingError("Can only parse BatteryCyclerExperiment")

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.

        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """
        retrieved_temporary_folder = kwargs["retrieved_temporary_folder"]
        output_json_filename = self.node.get_option("output_filename") + ".json"
        output_zip_filename = os.path.join(
            retrieved_temporary_folder, self.node.get_option("output_filename") + ".zip"
        )

        files_retrieved = self.retrieved.list_object_names()

        # Check that zip file is present
        if os.path.isfile(output_zip_filename):
            try:
                self.logger.debug(f"Storing '{output_zip_filename}'")
                output_raw_data_node = SinglefileData(output_zip_filename)
                self.out("raw_data", output_raw_data_node)
                output_raw_data_node_created = True
            except Exception:
                self.logger.warning(
                    f"The raw data zip file '{output_zip_filename}' could not be read."
                )
                output_raw_data_node_created = False
        else:
            self.logger.warning(
                f"The raw data zip file '{output_zip_filename}' is missing."
            )
            output_raw_data_node_created = False

        # Check that json file is present
        if not output_json_filename in files_retrieved:
            self.logger.error(
                f"The output json file '{output_json_filename}' is missing."
            )
            if output_raw_data_node_created:
                return self.exit_codes.ERROR_MISSING_JSON_FILE
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # If a json file was found, parse it and add output node
        try:
            self.logger.debug(f"Parsing '{output_json_filename}'")
            with self.retrieved.open(output_json_filename, "r") as handle:
                output_results_node = self.parse_tomato_results(
                    json.load(handle), self.logger
                )
            self.out("results", output_results_node)
        except Exception:
            self.logger.error(f"Error parsing json file '{output_json_filename}'.")
            return self.exit_codes.ERROR_PARSING_JSON_FILE

        # check that the zip file is there. Is it already stored in a SinglefileData node??
        if not output_raw_data_node_created:
            return self.exit_codes.ERROR_MISSING_ZIP_FILE

        # TODO: other checks:  jobs completed with error or cancelled
        # ......

        return ExitCode(0)

    @staticmethod
    def parse_tomato_results(data_dic, logger=None):
        """
        Parse results.json file.

        :returns: a :class:`aiida.orm.ArrayData` in this way:
          - `metadata` is stored as attribute
          - `data` is split in steps, physical quantity name, and n/s/u identifier (nominal value, std error, units)
            The name of each array is:  `'step{step_number}_{raw_quantity_name}_{identifier}'`
        """
        array_dic = {}
        for imstep, mstep in enumerate(data_dic["steps"]):  # method step
            raw_qty_names = list(mstep["data"][0]["raw"].keys())
            if logger:
                logger.debug(
                    f"parse_tomato_results: step {imstep}: {list(raw_qty_names)}"
                )
            for raw_qty_name in raw_qty_names:
                # substitute any special character with underscores
                raw_qty_name_cleaned = re.sub("[^0-9a-zA-Z_]", "_", raw_qty_name)
                if isinstance(mstep["data"][0]["raw"][raw_qty_name], dict):
                    for identifier in mstep["data"][0]["raw"][raw_qty_name].keys():
                        array_dic[
                            f"step{imstep}_{raw_qty_name_cleaned}_{identifier}"
                        ] = np.array(
                            [
                                step["raw"][raw_qty_name][identifier]
                                for step in mstep["data"]
                            ]
                        )
                else:
                    array_dic[f"step{imstep}_{raw_qty_name_cleaned}"] = np.array(
                        [step["raw"][raw_qty_name] for step in mstep["data"]]
                    )
            array_dic[f"step{imstep}_uts"] = np.array(
                [step["uts"] for step in mstep["data"]]
            )
        if logger:
            logger.debug(
                f"parse_tomato_results: arrays stored: {list(array_dic.keys())}"
            )

        node = ArrayData()
        for key, value in array_dic.items():
            node.set_array(key, value)
            node.set_attribute_many(data_dic["metadata"])

        return node
