

from pkg_resources import parse_requirements
from setuptools import setup

with open("requirements.txt") as req_file:
    install_reqs = list(parse_requirements(req_file.readlines()))

setup(
    name="lrs",
    version="0.0.1",
    author="ADL",
    packages=['lrs'],
    install_requires=list(map(str, install_reqs)),
)
