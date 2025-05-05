from setuptools import setup, find_packages

setup(
    name="ambulance_allocation",
    version="0.1.0",
    description="Ambulance allocation optimization models",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(include=["src", "src.*"]),
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.1.0",
        "gurobipy>=9.1.0",
        "matplotlib>=3.3.0",
        "networkx>=2.5.0",
    ],
)