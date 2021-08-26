#!/bin/bash

jupyter nbconvert --to=html --ExecutePreprocessor.timeout=1200 --execute notebooks/export.ipynb