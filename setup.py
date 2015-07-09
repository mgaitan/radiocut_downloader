#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

version = "0.2.1"

readme = open('README.rst').read()

setup(
    name='radiocut_downloader',
    version=version,
    description="""Download audiocuts from radiocut.fm""",
    long_description=readme,
    author='Martín Gaitán',
    author_email='gaitan@gmail.com',
    url='https://github.com/mgaitan/radiocut_downloader',
    packages = find_packages(),
    license="BSD",
    zip_safe=False,
    install_requires = ['docopt', 'pyquery', 'requests', 'moviepy'],
    entry_points={
        'console_scripts': [
            'radiocut = radiocut:main',
        ]},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)