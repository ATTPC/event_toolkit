# event_toolkit

This repository contains utilities for handling issues with raw AT-TPC data. Currently, it contains a script for correcting mismatched event numbers between the FRIBDAQ and GETDAQ data and correcting the HDF5 files in place. But more utilities will be added as need arises!

## Install

Download the repository using `git clone https://github.com/attpc/event_toolkit.git`. Create a virtual environment using `python -m venv .venv`. Activate the environment, and then install all dependencies using `pip install -r requirements.txt`. In some cases, different install methods may be needed (particularly Windows). The instructions [here](https://attpc.github.io/Spyral/user_guide/getting_started/) for setting up Python and an environment should be helpful.

## Available Tools

### event_fixer

This tool is aimed at repairing mismatched event numbers between FRIBDAQ and GETDAQ. It will also correct runs where the MuTaNT board was not properly reset between runs. It checks the GET data first, ensuring that those events start at 0 and shifting all events as appropriate. The FRIBDAQ data is then checked, and corrected such that event numbers match the GET data. Finally, after the corrections are applied, the timestamps between events are compared to make sure that the events are actually correlated in time.

The usage is `python event_fixer.py </your/data/directory/> <first_run> <last_run>` with the event_toolkit virtual environment active. Replace `</your/data/directory/>` with the path to your merged AT-TPC HDF5 files, `<first_run>` with the first run number to be analyzed (inclusive) and `<last_run>` with the last run number to be analyzed (inclusive).

## Requirements

Compatible with Python 3.10 through 3.12

Dependencies:

- [click](https://click.palletsprojects.com/en/8.1.x/)
- [tqdm](https://tqdm.github.io/)
- [h5py](https://www.h5py.org/)
