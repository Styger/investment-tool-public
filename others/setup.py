# setup.py im Projektordner (wo auch main.py liegt)
from setuptools import setup, find_packages

setup(
    name="investment_tool",
    version="0.1",
    packages=find_packages(),  # wichtig: das scannt alle Ordner mit __init__.py
    include_package_data=True,
)
