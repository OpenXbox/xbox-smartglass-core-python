#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name="xbox-smartglass-core",
    version="1.0.5",
    author="OpenXbox",
    description="A library to interact with the Xbox One gaming console via the SmartGlass protocol.",
    long_description=open('README.rst').read() + '\n\n' + open('HISTORY.rst').read(),
    license="GPL",
    keywords="xbox one smartglass",
    url="https://github.com/OpenXbox/xbox-smartglass-core-python",
    packages=[
        'xbox.sg',
        'xbox.sg.utils',
        'xbox.sg.scripts',
        'xbox.sg.packet'
    ],
    namespace_packages=['xbox'],
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6"
    ],
    install_requires=[
        'xbox-webapi',
        'construct==2.9.45',
        'cryptography',
        'appdirs',
        'gevent',
        'urwid',
        'dpkt'
    ],
    tests_require=[
        'pytest',
        'flake8',
        'tox'
    ],
    extras_require={
        'dev': [
            'bumpversion',
            'watchdog',
            'coverage',
            'Sphinx',
            'wheel',
            'twine'
        ]
    },
    test_suite="tests",
    entry_points={
        'console_scripts': [
            'xbox-pcap=xbox.sg.scripts.pcap:main',
            'xbox-discover=xbox.sg.scripts.discover:main',
            'xbox-poweron=xbox.sg.scripts.poweron:main',
            'xbox-poweroff=xbox.sg.scripts.poweroff:main',
            'xbox-client=xbox.sg.scripts.client:main',
            'xbox-recrypt=xbox.sg.scripts.recrypt:main',
            'xbox-text=xbox.sg.scripts.text:main',
            'xbox-input=xbox.sg.scripts.input:main',
            'xbox-tui=xbox.sg.scripts.tui:main',
        ]
    }
)
