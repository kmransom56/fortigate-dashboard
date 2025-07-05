from setuptools import setup, find_packages

setup(
    name="fortinet-mcp-server",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "redis",
        "certifi",
    ],
    entry_points={
        "console_scripts": [
            "fortinet-mcp=fortinet_server_enhanced:main",
        ],
    },
    author="Keith Ransom",
    author_email="keith.ransom@example.com",
    description="Fortinet MCP Server for FortiGate API integration",
    long_description="""Fortinet MCP Server provides seamless integration with FortiGate APIs, enabling advanced network management capabilities.""",
    long_description_content_type="text/markdown",
    url="https://github.com/kmransom56/fortinet-mcp-server",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
