"""
Build script for Mac and Windows. 
Usage (Mac OS X):
 python setup.py py2app -A

Usage (Windows):
 python setup.py py2exe
"""
import sys
from setuptools import setup

# Define platform for setup based on OS
if sys.platform == 'darwin':
    setup_requires = 'py2app'
elif sys.platform == 'win32':
    setup_requires = 'py2exe'

# Define Attributes
NAME = 'Password Manager'
APP = ['src/log_in.py']
DATA_FILES = ['--iconfile']
OPTIONS = {'iconfile': '/Users/avivfaraj/Desktop/Project/9/img/img.icns'}

# Make setup
setup(
    name = NAME,
    app = APP,
    data_files = DATA_FILES,
    options = {setup_requires: OPTIONS},
    setup_requires = [setup_requires],
)