#!/bin/bash

bundle exec jekyll build
mv _site/base.html ecosante/templates/base.html