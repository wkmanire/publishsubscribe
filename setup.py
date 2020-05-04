from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="publishsubscribe",
    version="1.1.1",
    description="A pubsub library built specifically with game mechanics in mind.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wkmanire/publishsubscribe",
    author="wkmanire",
    author_email="williamkmanire@gmail.com",
    py_modules=["publishsubscribe"],
    python_requires=">=3.8",
)
