try:
    from setuptools import setup
except ImportError :
    raise ImportError("setuptools module required, please go to https://pypi.python.org/pypi/setuptools and follow the instructions for installing setuptools")

setup(
    name='parseratorvariable',
    url='https://github.com/datamade/parseratorvariables',
    version='0.0.17',
    description='Structured variable type for dedupe',
    packages=['parseratorvariable'],
    install_requires=['dedupe>=1.0.0',
                      "backports.functools_lru_cache; python_version<'3.2'",
                      'numpy',
                      'probableparsing'],
    license='The MIT License: http://www.opensource.org/licenses/mit-license.php'
    )
