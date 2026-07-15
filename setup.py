from setuptools import setup, find_packages

setup(
    name="docker-avd-manager",
    version="1.0.0",
    description="Manage Android Virtual Devices inside Docker containers",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "avd-manager=src.cli:main",
        ],
    },
)
