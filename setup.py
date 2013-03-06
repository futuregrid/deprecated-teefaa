#from distribute_setup import use_setuptools
#use_setuptools(version="0.6.15")
from setuptools import setup, find_packages
import sys
sys.path.insert(0, './src')
from teefaa import RELEASE

version = open("VERSION.txt").read()

classifiers = """\
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Science/Research
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: Apache Software License
Programming Language :: Python
Topic :: Database
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: POSIX :: Linux
Programming Language :: Python :: 2.7
Operating System :: MacOS :: MacOS X
Topic :: Scientific/Engineering
Topic :: System :: Clustering
Topic :: System :: Distributed Computing
"""


setup(
    name='teefaa',
    version=version,
    description = "Futuregrid Teefaa is a set of tools that enables simplified provisioning from repository or directly from running virtual/baremetal machines.",
    classifiers = filter(None, classifiers.split("\n")),
    keywords='FutureGrid, Teefaa',
    maintainer='Koji Tanaka, Javier Diaz, Gregor von Laszewski',
    maintainer_email="kj.tanaka@gmail.com",
    author='Koji Tanaka',
    author_email='kj.tanaka@gmail.com',
    url='https://github.com/futuregrid/teefaa',
    license='Apache 2.0',
    package_dir = {'': 'src'},
    packages = find_packages('src'),
    
    #include_package_data=True,
    zip_safe=False,

    entry_points={
        'console_scripts': [
                'teefaa = teefaa.teefaa:main',
             ]},

    install_requires = [
             'setuptools',
             'pip',
             'paramiko',
             'boto',
             'argparse',
             'PyYAML',
             ],
    )
