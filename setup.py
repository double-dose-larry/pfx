from setuptools import setup

setup(
   name='pfx',
   version='0.01',
   description='Python library to grab MLB PitchF/X data',
   author='double_dose_larry',
   author_email='larrydouble33@gmail.com',
   packages=['pfx'],  #same as name
   install_requires=['bs4', 'requests', 'pandas'], #external packages as dependencies
)