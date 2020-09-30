from setuptools import setup
from setuptools import find_packages

setup(name='eddylicious',
      version='0.1.0',
      description='A package for generating inflow fields for LES and DNS',
      url='https://github.com/timofeymukha/eddylicious',
      author='Timofey Mukha',
      author_email='timofey.mukha@it.uu.se',
      packages=find_packages(),
      entry_points = {
          'console_scripts':[
              'inflowStats=eddylicious.bin.inflowStats:main',
              'precursorStats=eddylicious.bin.precursorStats:main',
              'runLundRescaling=eddylicious.bin.runLundRescaling:main',
              'runInterpolation=eddylicious.bin.runInterpolation:main',
              'runRandomFluctuations=eddylicious.bin.runRandomFluctuations:main',
              'convertFoamFileToHDF5=eddylicious.bin.convertFoamFileToHDF5:main'
                            ]
      },
      install_requires=[
                    'numpy',
                    'scipy',
                    'matplotlib',
                    'mock',
                    'sphinxcontrib-bibtex',
                       ],
      license="GNU GPL 3",
      classifiers=[
          "Development Status :: 4 - Beta",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
      ],
      zip_safe=False)

