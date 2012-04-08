import os
from setuptools import setup

README = os.path.join(os.path.dirname(__file__), 'README.rst')

setup_args = dict(
    name='potpy',
    version = '0.0.1',
    description=('A general purpose routing apparatus.'),
    long_description = open(README).read() + '\n\n',
    author='David Zuwenden',
    author_email='dhain@zognot.org',
    url='https://github.com/dhain/potpy',
    license='MIT',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=['potpy'],
    test_suite='potpy.test',
    test_loader='potpy.test.loader:Loader',
    tests_require=['mock'],
)

if __name__ == '__main__':
    setup(**setup_args)
