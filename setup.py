"""
Setup configuration for Ethereum Transaction Interceptor
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="eth-transaction-interceptor",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Advanced transaction interceptor and simulator for Ethereum",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/eth-transaction-interceptor",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.10.0",
        "eth-utils>=4.0.0",
        "flask>=3.0.0",
        "requests>=2.31.0",
        "colorama>=0.4.6",
        "odfpy>=1.4.1",
        "rlp>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "eth-interceptor=eth_interceptor.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "eth_interceptor": ["config/*.json.example"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/eth-transaction-interceptor/issues",
        "Source": "https://github.com/yourusername/eth-transaction-interceptor",
    },
)