from setuptools import setup, find_packages

with open("requirements.txt") as requirement_file:
    requirements = requirement_file.read().split()

setup(
    name="impossible_dialogue",
    description="The (Im)possible Dialogue project",
    version="1.0.0",
    install_requires=requirements,
    packages=find_packages(exclude=["project1", "project2"]), # package = any folder with an __init__.py file
)