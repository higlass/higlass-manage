from setuptools import setup

setup(
    name='higlass-manage',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    url='https://github.com/pkerpedjiev/higlass-manage',
    description='Wrappers for running the HiGlass Docker container',
    version='0.1.7',
    py_modules=['higlass_manage'],
    install_requires=[
        'Click',
        'clodius==0.9.0',
        'cooler==0.7.9',
        'pandas>=0.19',
        'docker',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        higlass-manage=higlass_manage:cli
    ''',
)
