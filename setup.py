"""Setup configuration for the Lyra marketing system."""

from setuptools import setup, find_packages

setup(
    name="lyra-marketing",
    version="0.1.0",
    description="Marketing system for junk removal businesses",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "lyra=lyra.cli:main",
        ],
    },
)
