import os
from setuptools import setup, find_packages

version = '0.0.1'
README = os.path.join(os.path.dirname(__file__), 'README.rst')
long_description = open(README).read() + '\n\n'

if __name__ == '__main__':
    setup(
        name='todo',
        version=version,
        description=(''),
        long_description=long_description,
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
        packages=find_packages(),
        test_suite='todo.test',
        tests_require=['mock', 'wsgi_intercept', 'pastedeploy'],
        install_requires=['potpy', 'webob'],
        entry_points={
            'paste.app_factory': [
                'main=todo.app_factory:factory',
            ],
        }
    )
