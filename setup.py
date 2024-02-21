# pip install setuptools twine
# python setup.py sdist bdist_wheel
# twine upload --repository testpypi dist/*
# 'backtrader @ git+https://github.com/WISEPLAT/backtrader.git' - was removed from install_requires, as it can't publish
# twine upload --repository pypi dist/*
import os.path
import codecs  # To use a consistent encoding
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the relevant file
with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='backtrader_finam',
      version='2.0.4',
      author='wiseplat',
      author_email='oshpagin@gmail.com',
      license='MIT License',
      description='API Finam integration with Backtrader',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/WISEPLAT/backtrader_finam',
      packages=find_packages(exclude=['docs', 'examples', 'ConfigFinam']),
      install_requires=['pandas', 'matplotlib', 'numpy', 'backtrader', 'requests', 'websockets', 'pytz', 'grpcio', 'protobuf', 'types-protobuf', 'googleapis-common-protos'],
      dependency_links=['https://github.com/WISEPLAT/FinamPy/tree/master#egg=FinamPy'],
      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 5 - Production/Stable',

          # Indicate who your project is intended for
          'Intended Audience :: Developers',
          'Intended Audience :: Financial and Insurance Industry',

          # Indicate which Topics are covered by the package
          'Topic :: Software Development',
          'Topic :: Office/Business :: Financial',

          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent'
      ],
      keywords=['trading', 'development'],
      project_urls={
          'Documentation': 'https://github.com/WISEPLAT/backtrader_finam/blob/master/README.md'
      },
      python_requires='>=3.7'
      )
