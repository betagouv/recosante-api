#!/bin/bash
git pull
pip install .
alembic upgrade head