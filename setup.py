from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='subssh.app.vcs',
      version=version,
      description="Version control management made simple",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['subssh', 'subssh.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'subssh',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
