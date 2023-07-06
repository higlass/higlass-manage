from setuptools import setup

setup(
    name="higlass-manage",
    author="Peter Kerpedjiev",
    author_email="pkerpedjiev@gmail.com",
    url="https://github.com/pkerpedjiev/higlass-manage",
    description="Wrappers for running the HiGlass Docker container",
    version="0.8.2",
    py_modules=["higlass_manage"],
    packages=["higlass_manage"],
    package_data={"": ["redis/*"]},
    include_package_data=True,
    install_requires=[
        "Click",
        "clodius>=0.10.3",
        "cooler>=0.8.2",
        "pandas>=0.19",
	    "higlass-python>=1.0.0",
        "docker",
        "requests",
    ],
    entry_points="""
        [console_scripts]
        higlass-manage=higlass_manage.cli:cli
    """,
)
