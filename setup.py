#!/usr/scripts/env python

from setuptools import setup, find_packages

setup(
    name="tecplot-tools",
    version="0.0.0",
    packages=find_packages(
        where="lib",
        include="tecplot_utilities/*"
    ),
    package_dir={"": "lib"},
    install_requires=[
        "typer",
        "rich",
        "numpy"
    ],
    entry_points="""
    [console_scripts]
    extract-multizone-tec=tecplot_utilities.main:entry_point
    """
)
