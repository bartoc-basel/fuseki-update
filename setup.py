from setuptools import setup
import os
import re


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('pyfusekiutil/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name='pyfusekiutil',
    version=version,
    description='Manage a Fuseki-Triple Store',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/bartoc-basel/fuseki-update',
    author='Jonas Waeber',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='fuseki triple-store skos skosmos skosify',
    packages=['pyfusekiutil'],
    install_requires=['pygsheets', 'rdflib', 'SPARQLWrapper', 'requests', 'skosify'],
    entry_points={
        'console_scripts': ['pyfuseki = pyfusekiutil.cli:main']
    }
)