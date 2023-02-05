#!/bin/bash
yarn install
pip install -e .[test]
flask db upgrade
flask run --host=0.0.0.0