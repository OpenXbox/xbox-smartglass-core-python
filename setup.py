#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name="xbox-smartglass-core",
    version="1.1.1",
    author="OpenXbox",
    description="A library to interact with the Xbox One gaming console via the SmartGlass protocol.",
    long_description=open('README.rst').read() + '\n\n' + open('HISTORY.rst').read(),
    long_description_content_type="text/x-rst",
    license="GPL",
    keywords="xbox one smartglass auxiliary fallout title stump tv streaming livetv rest api",
    url="https://github.com/OpenXbox/xbox-smartglass-core-python",
    packages=[
        'xbox.sg',
        'xbox.sg.utils',
        'xbox.sg.scripts',
        'xbox.sg.packet',
        'xbox.auxiliary',
        'xbox.auxiliary.scripts',
        'xbox.stump',
        'xbox.rest',
        'xbox.rest.routes',
        'xbox.rest.scripts'
    ],
    namespace_packages=['xbox'],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    install_requires=[
        'xbox-webapi>=1.1.8',
        'construct==2.10.56',
        'cryptography==2.8',
        'gevent==1.5a3',
        'dpkt',
        'aenum;python_version<="3.5"',
        'marshmallow-objects',
        'Flask'
    ],
    tests_require=[
        'pytest',
        'flake8',
        'tox'
    ],
    extras_require={
        'dev': [
            'bump2version',
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
            'xbox-fo4-relay=xbox.auxiliary.scripts.fo4:main',
            'xbox-rest-server=xbox.rest.scripts.rest_server:main'
        ]
    }
)
