#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages

setup(
    name="xbox-smartglass-core",
    version="1.3.0",
    author="OpenXbox",
    author_email="noreply@openxbox.org",
    description="A library to interact with the Xbox One gaming console via the SmartGlass protocol.",
    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.md').read(),
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="xbox one smartglass auxiliary fallout title stump tv streaming livetv rest api",
    url="https://github.com/OpenXbox/xbox-smartglass-core-python",
    python_requires=">=3.7",
    packages=find_namespace_packages(include=['xbox.*']),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    test_suite="tests",
    install_requires=[
        'xbox-webapi==2.0.9',
        'construct==2.10.56',
        'cryptography==3.2.1',
        'dpkt==1.9.4',
        'pydantic==1.7.1',
        'aioconsole==0.3.0',
        'fastapi==0.61.1',
        'uvicorn==0.12.2',
        'urwid==2.1.2'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-console-scripts', 'pytest-asyncio'],
    extras_require={
        "dev": [
            "pip",
            "bump2version",
            "wheel",
            "watchdog",
            "flake8",
            "coverage",
            "Sphinx",
            "sphinx_rtd_theme",
            "recommonmark",
            "twine",
            "pytest",
            "pytest-asyncio",
            "pytest-console-scripts",
            "pytest-runner",
        ],
    },
    entry_points={
        'console_scripts': [
            'xbox-cli=xbox.scripts.main_cli:main',
            'xbox-discover=xbox.scripts.main_cli:main_discover',
            'xbox-poweron=xbox.scripts.main_cli:main_poweron',
            'xbox-poweroff=xbox.scripts.main_cli:main_poweroff',
            'xbox-repl=xbox.scripts.main_cli:main_repl',
            'xbox-replserver=xbox.scripts.main_cli:main_replserver',
            'xbox-textinput=xbox.scripts.main_cli:main_textinput',
            'xbox-gamepadinput=xbox.scripts.main_cli:main_gamepadinput',
            'xbox-tui=xbox.scripts.main_cli:main_tui',
            'xbox-fo4-relay=xbox.scripts.main_cli:main_falloutrelay',
            'xbox-pcap=xbox.scripts.pcap:main',
            'xbox-recrypt=xbox.scripts.recrypt:main',
            'xbox-rest-server=xbox.scripts.rest_server:main'
        ]
    }
)
