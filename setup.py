import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = fh.read().splitlines()

setuptools.setup(
    name="mcontrol",
    version="0.0.0",
    author="Juan Pablo Crossley",
    author_email=["juan.crossley@mongodb.com"],
    py_modules=["mcontrol"],
    description="A commmand line tool to create replicasets for testing using files instead of arguments.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mongodb-ps/mcontrol",
    packages=setuptools.find_namespace_packages(exclude=["tests"]),
    package_dir={"mcontrol": "mcontrol"},
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
           'mcontrol=mcontrol.main:main'
        ]
    },
    python_requires=">=3.6",
)

