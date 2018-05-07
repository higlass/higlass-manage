from setuptools import setup

setup(
    name='higlass-manage',
    version='0.1.1',
    py_modules=['higlass_manage'],
    install_requires=[
        'Click',
        'hgtiles==v0.2.1',
        'clodius==v0.8.0'
    ],
    entry_points='''
        [console_scripts]
        higlass-manage=higlass_manage:cli
    ''',
)
