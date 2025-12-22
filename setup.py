#!/usr/bin/env python
"""Setup script for solar-om-analytics package."""
from setuptools import setup, find_packages

setup(
    packages=find_packages(include=["src.logic*", "src.ui*"]),
    package_dir={"": "."},
)
