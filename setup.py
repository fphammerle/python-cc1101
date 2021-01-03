# python-cc1101 - Python Library to Transmit RF Signals via C1101 Transceivers
#
# Copyright (C) 2020 Fabian Peter Hammerle <fabian@hammerle.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pathlib

import setuptools

_REPO_URL = "https://github.com/fphammerle/python-cc1101"

setuptools.setup(
    name="cc1101",
    use_scm_version=True,
    packages=setuptools.find_packages(),
    description="Python Library & Command Line Tool to Transmit RF Signals via C1101 Transceivers",
    long_description=pathlib.Path(__file__).parent.joinpath("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Fabian Peter Hammerle",
    author_email="fabian+python-cc1101@hammerle.me",
    url=_REPO_URL,
    project_urls={"Changelog": _REPO_URL + "/blob/master/CHANGELOG.md"},
    license="GPLv3+",
    keywords=[
        "ISM",
        "SPI",
        "automation",
        "radio-frequency",
        "raspberry-pi",
        "transceiver",
        "transmission",
        "wireless",
    ],
    classifiers=[
        # https://pypi.org/classifiers/
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        # .github/workflows/python.yml
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Home Automation",
        "Topic :: Communications",
    ],
    entry_points={
        "console_scripts": [
            "cc1101-export-config = cc1101._cli:_export_config",
            "cc1101-transmit = cc1101._cli:_transmit",
        ]
    },
    # apt install python3-spidev
    # https://github.com/doceme/py-spidev
    install_requires=["spidev"],
    setup_requires=["setuptools_scm"],
    tests_require=["pytest"],
)
