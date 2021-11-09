#!/bin/bash

SCRIPT=`realpath $0`
SCRIPTPATH=$(dirname "$SCRIPT")
jupyter nbconvert --to=html --ExecutePreprocessor.timeout=1200 --execute $SCRIPTPATH/notebooks/export.ipynb