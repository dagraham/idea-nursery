# setup.py
import os

from setuptools import find_packages, setup


def read_version():
    with open("modules/__version__.py") as f:
        for line in f:
            if line.startswith("version"):
                # Extract the version string
                return line.split("=")[1].strip().strip("'")

readme_path = os.path.join(os.path.dirname(__file__), 'modules', 'README.txt')
with open(readme_path, "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="idea-nursery",  # Replace with your app's name
    version=read_version(),
    author="Daniel A Graham",  # Replace with your name
    author_email="dnlgrhm@gmail.com",  # Replace with your email
    description="XXX.",
    # long_description=open("README.md").read(),  # If you have a README file
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dagraham/idea-nursery",  # Replace with the repo URL if applicable
    packages=find_packages(),
    include_package_data=True,  # Include non-Python files specified in MANIFEST.in
    package_data={
        'trf': ['README.txt'],  # Ensure README.txt is included in the trf package
    },    # py_modules=["trf"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace with your license
        "Operating System :: OS Independent",/
    ],
    python_requires=">=3.9.0",  # Specify the minimum Python version
    install_requires=[
        'XXX',
        'prompt-toolkit>=3.0.24',
        'ruamel.yaml>=0.15.88',
        'python-dateutil>=2.7.3',
        'persistent>=4.6.4',  # Add persistent here
        'ZODB>=5.6.0',  # Add ZODB here
        'transaction>=3.0.1',  # Add transaction here
        'lorem>=0.1.1',
        'pyperclip>=1.7.0',
    ],
    entry_points={
        'console_scripts': [
            'trf=trf.__main__:main',  # Correct the path to `main` in `trf/trf.py`
        ],
    },
)
