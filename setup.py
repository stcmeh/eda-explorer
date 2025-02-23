# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2025, Spyder Bot
#
# Licensed under the terms of the Not open source
# ----------------------------------------------------------------------------
"""
EDA Explorer setup.
"""
from setuptools import find_packages
from setuptools import setup

from eda_explorer import __version__


setup(
    # See: https://setuptools.readthedocs.io/en/latest/setuptools.html
    name="eda-explorer",
    version=__version__,
    author="Spyder Bot",
    author_email="spyder.python@gmail.com",
    description="EDA Explorer Spyder Widget",
    license="Not open source",
    url="https://github.com/spyder-bot/eda-explorer",
    python_requires='>= 3.7',
    install_requires=[
        "qtpy",
        "qtawesome",
        "spyder>=5.0.1",
    ],
    packages=find_packages(),
    entry_points={
        "spyder.plugins": [
            "eda_explorer = eda_explorer.spyder.plugin:EDAExplorer"
        ],
    },
    classifiers=[
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
    ],
)
