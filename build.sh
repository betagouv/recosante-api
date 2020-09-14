#!/bin/bash

bundle exec jekyll build
ls -al
mv _site/base.html ecosante/templates/base.html