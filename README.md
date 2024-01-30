[![Build Status](https://github.com/epfl-theos/aiida-aurora/workflows/ci/badge.svg?branch=main)](https://github.com/epfl-theos/aiida-aurora/actions)
[![Coverage Status](https://coveralls.io/repos/github/epfl-theos/aiida-aurora/badge.svg?branch=main)](https://coveralls.io/github/epfl-theos/aiida-aurora?branch=main)
[![Docs status](https://readthedocs.org/projects/aiida-aurora/badge)](http://aiida-aurora.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-aurora.svg)](https://badge.fury.io/py/aiida-aurora)

# aiida-aurora

AiiDA plugin for the Aurora project (autonomous robotic battery innovation platform).
A collaboration between EPFL & Empa, within the BIG-MAP Stakeholder Initiative Call 2021-2023.

## Repository contents

- [`.github/`](.github/): [Github Actions](https://github.com/features/actions) configuration
  - [`ci.yml`](.github/workflows/ci.yml): runs tests, checks test coverage and builds documentation at every new commit
  - [`publish-on-pypi.yml`](.github/workflows/publish-on-pypi.yml): automatically deploy git tags to PyPI - just generate a [PyPI API token](https://pypi.org/help/#apitoken) for your PyPI account and add it to the `pypi_token` secret of your github repository
- [`aiida_aurora/`](aiida_aurora/): The main source code of the plugin package
  - [`data/`](aiida_aurora/data/): A new `DiffParameters` data class, used as input to the `DiffCalculation` `CalcJob` class
  - [`calculations.py`](aiida_aurora/calculations.py): A new `DiffCalculation` `CalcJob` class
  - [`cli.py`](aiida_aurora/cli.py): Extensions of the `verdi data` command line interface for the `DiffParameters` class
  - [`helpers.py`](aiida_aurora/helpers.py): Helpers for setting up an AiiDA code for `diff` automatically
  - [`parsers.py`](aiida_aurora/parsers.py): A new `Parser` for the `DiffCalculation`
- [`docs/`](docs/): A documentation template ready for publication on [Read the Docs](http://aiida-diff.readthedocs.io/en/latest/)
- [`examples/`](examples/): An example of how to submit a calculation using this plugin
- [`tests/`](tests/): Basic regression tests using the [pytest](https://docs.pytest.org/en/latest/) framework (submitting a calculation, ...). Install `pip install -e .[testing]` and run `pytest`.
- [`.coveragerc`](.coveragerc): Configuration of [coverage.py](https://coverage.readthedocs.io/en/latest) tool reporting which lines of your plugin are covered by tests
- [`.gitignore`](.gitignore): Telling git which files to ignore
- [`.pre-commit-config.yaml`](.pre-commit-config.yaml): Configuration of [pre-commit hooks](https://pre-commit.com/) that sanitize coding style and check for syntax errors. Enable via `pip install -e .[pre-commit] && pre-commit install`
- [`.readthedocs.yml`](.readthedocs.yml): Configuration of documentation build for [Read the Docs](https://readthedocs.org/)
- [`LICENSE`](LICENSE): License for your plugin
- [`MANIFEST.in`](MANIFEST.in): Configure non-Python files to be included for publication on [PyPI](https://pypi.org/)
- [`README.md`](README.md): This file

## Installation

```shell
pip install aiida-aurora
verdi quicksetup  # better to set up a new profile
verdi plugin list aiida.calculations  # should now show your calclulation plugins
```

## Usage

Here goes a complete example of how to submit a test calculation using this plugin.

A quick demo of how to submit a calculation:

```shell
verdi daemon start     # make sure the daemon is running
cd examples
./example_01.py        # run test calculation
verdi process list -a  # check record of calculation
```

The plugin also includes verdi commands to inspect its data types:

```shell
verdi data aurora list
verdi data aurora export <PK>
```

## Development

```shell
git clone https://github.com/epfl-theos/aiida-aurora .
cd aiida-aurora
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

See the [developer guide](http://aiida-aurora.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT

## Acknowledgements

This project was supported by the Open Research Data Program of the ETH Board.

## Contact

- Edan Bainglass (edan.bainglass@psi.ch)
- Francisco F. Ramirez (ramirezfranciscof@gmail.com)
- Loris Ercole (loris.ercole@gmail.com)
- Giovanni Pizzi (giovanni.pizzi@psi.ch)
