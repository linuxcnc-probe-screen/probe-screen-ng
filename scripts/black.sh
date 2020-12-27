#!/bin/bash

# Determine absolute path to folder this script is in
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Run psng/psng.py through the `black` code formatting tool.
docker run -v $SCRIPTPATH/../:/code cytopia/black -- /code/psng/python/ /code/.axisrc
