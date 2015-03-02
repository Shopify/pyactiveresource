from setuptools import setup
import sys

version = '2.1.1'

if sys.version_info >= (3,):
    python_dateutils_version = 'python-dateutil>=2.0'
else:
    python_dateutils_version = 'python-dateutil<2.0'


setup(name='pyactiveresource',
      version=version,
      description='ActiveResource for Python',
      author='Shopify',
      author_email='developers@shopify.com',
      url='https://github.com/Shopify/pyactiveresource/',
      packages=['pyactiveresource', 'pyactiveresource/testing'],
      license='MIT License',
      test_suite='test',
      install_requires=[
          'six',
      ],
      tests_require=[
          python_dateutils_version,
          'PyYAML',
      ],
      platforms=['any'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Topic :: Software Development', 
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Software Development :: Libraries :: Python Modules']
    )
