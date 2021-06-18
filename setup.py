from setuptools import setup
try:
    from pip._internal.req import parse_requirements
except ImportError:
    from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)

setup(
    name = "lrs",
    version = "0.0.0",
    author = "ADL",
    packages=['lrs'],
    install_requires=[
        str(ir.requirement if hasattr(ir, "requirement") else ir.req)
        for ir in install_reqs
    ],
)
