from setuptools import setup
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)

setup(
    name = "lrs",
    version = "0.0.0",
    author = "ADL",
    packages=['lrs'],
    install_requires=[str(ir.req) for ir in install_reqs],
)
