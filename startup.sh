#!/bin/bash
yarn install
pip install -e .
flask db upgrade
flask run