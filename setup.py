from pip.req import parse_requirements
from setuptools import setup

# from https://stackoverflow.com/questions/14399534/reference-requirements-txt-for-the-install-requires-kwarg-in-setuptools-setup-py
install_reqs = parse_requirements('requirements.txt')

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='higlass-manage',
    version='0.1',
    py_modules=['higlass_manage'],
    install_requires=reqs,
    entry_points='''
        [console_scripts]
        higlass-manage=higlass_manage:cli
    ''',
)
