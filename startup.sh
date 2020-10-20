#!/bin/bash
flask db upgrade
uwsgi wsgi.ini