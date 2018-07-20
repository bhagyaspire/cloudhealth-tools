#!/bin/bash
# Quick and dirty script to publish new version to pypi

rm dist/*
python setup.py sdist
twine upload dist/*
