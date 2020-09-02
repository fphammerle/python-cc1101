import pathlib

import setuptools

_REPO_URL = "https://github.com/fphammerle/python-cc1101"

setuptools.setup(
    name="cc1101",
    use_scm_version=True,
    packages=setuptools.find_packages(),
    description="Python Library for CC1101 Transceivers",
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
        # TODO .github/workflows/python.yml
        # "Programming Language :: Python :: 3.5",
        # "Programming Language :: Python :: 3.6",
        # "Programming Language :: Python :: 3.7",
        # "Programming Language :: Python :: 3.8",
        "Topic :: Home Automation",
        "Topic :: Communications",
    ],
    # apt install python3-spidev
    # https://github.com/doceme/py-spidev
    install_requires=["spidev"],
    setup_requires=["setuptools_scm"],
    tests_require=["pytest"],
)
