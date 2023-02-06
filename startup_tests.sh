#!/bin/bash
yarn install
pip install -e .[test]
pytest .