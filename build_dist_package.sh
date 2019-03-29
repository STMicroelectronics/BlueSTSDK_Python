#!/bin/sh
python setup.py sdist bdist_wheel && python -m twine upload --skip-existing --verbose dist/*
