from setuptools import setup

setup(
    name='higlass-manage',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    url='https://github.com/pkerpedjiev/higlass-manage',
    description='Wrappers for running the HiGlass Docker container',
    version='0.1.2',
    py_modules=['higlass_manage'],
    install_requires=[
        'Click',
        'hgtiles==v0.2.1',
        'clodius==v0.9.0',
        'docker'
    ],
    entry_points='''
        [console_scripts]
        higlass-manage=higlass_manage:cli
    ''',
)
