try:
    from setuptools import setup, Extension
except ImportError :
    raise ImportError("setuptools module required, please go to https://pypi.python.org/pypi/setuptools and follow the instructions for installing setuptools")

requirements = ['dedupe>=1.0.0',
                'future']

try:
    from functools import lru_cache
except ImportError:
    requirements += ['backports.lru_cache']


setup(
    name='parseratorvariable',
    url='https://github.com/datamade/parseratorvariables',
    version='0.0.17',
    description='Structured variable type for dedupe',
    packages=['parseratorvariable'],
    install_requires=requirements,
    license='The MIT License: http://www.opensource.org/licenses/mit-license.php'
    )
