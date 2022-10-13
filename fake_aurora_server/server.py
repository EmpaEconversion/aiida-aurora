#!/usr/bin/env python
"""This script emulates the Aurora's server API responding to requests."""

import argparse
import datetime
import json
from json import JSONDecodeError

import numpy as np


def measure(time, record_every_dt):
    """Simulates the measure of V and I."""
    times = np.arange(0.0, time + 0.0001, record_every_dt)
    data = {
        "time": times.tolist(),
        "V": np.sin(times).tolist(),
        "I": np.cos(times).tolist(),
    }
    return data


def execute_experiment(battery_d, experiment_d):
    """Execute the experiment and return a dictionary."""
    start_time = datetime.datetime.now()
    print(f"I am executing an experiment at {start_time}. My inputs are:")
    print(f"battery_d    = {battery_d}")
    print(f"experiment_d = {experiment_d}")

    # validate inputs
    if experiment_d["description"].get("technique") not in ("OCV", "CPLIMIT"):
        raise ValueError("Technique not valid.")

    # perform measurement
    output_data = measure(
        experiment_d["parameters"]["time"],
        experiment_d["parameters"]["record_every_dt"],
    )
    end_time = start_time + datetime.timedelta(seconds=output_data["time"][-1] + 1)

    # generate output dic
    results_d = {
        "start_time":
        str(start_time),
        "sequence": [
            {
                "technique": experiment_d["description"].get("technique"),
                "parameters": experiment_d["parameters"],
                "duration": output_data["time"][-1],
                "output_data": output_data,
            },
        ],
        "end_time":
        str(end_time),
    }
    return results_d


def main():
    """Aurora API emulator."""
    parser = argparse.ArgumentParser(
        description="This script emulates the Aurora's server API responding to requests.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("battery_specs", type=str, help="A JSON file with the battery specifications.")
    parser.add_argument(
        "experiment_specs",
        type=str,
        help="A JSON file with the experiment specifications.",
    )
    parser.add_argument("-o", "--output", type=str, default="exp.out", help="Name of the output file.")
    args = parser.parse_args()

    try:
        battery_specs = json.load(open(args.battery_specs))
        experiment_specs = json.load(open(args.experiment_specs))
    except JSONDecodeError as err:
        raise RuntimeError("Failed to open JSON file.") from err

    output_d = {}
    # try:
    output_d = execute_experiment(battery_specs, experiment_specs)
    # except Exception as err:
    #    print(f'Error during experiment: {type(err)}: {err}')
    #    output_d['exit_status'] = 1
    #    output_d['exit_msg'] = err
    # else:
    #    output_d['exit_status'] = 0
    #    output_d['exit_msg'] = None

    print(f"I am writing results to {args.output} ...")
    json.dump(output_d, open(args.output, "w"))
    print("Done.")


if __name__ == "__main__":
    main()
