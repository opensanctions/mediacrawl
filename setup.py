from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()


setup(
    name="mediacrawl",
    version="0.0.1",
    description="Crawl reporting from media web sites.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="crawler spider journalism text",
    author="Friedrich Lindenberg",
    author_email="friedrich@pudo.org",
    url="https://github.com/opensanctions/mediacrawl",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    namespace_packages=[],
    include_package_data=True,
    package_data={"": ["mediacrawl/py.typed"]},
    zip_safe=False,
    install_requires=[
        "sqlalchemy[asyncio]",
        "aiosqlite",
        "aiohttp[speedups]",
        "asyncpg",
        "pydantic",
        "pydantic_yaml",
        "articledata",
        "pantomime",
        "orjson",
        "pyyaml",
        "trafilatura",
        "langdetect",
        "languagecodes",
        "charset-normalizer",
        "shortuuid >= 1.0.1, < 2.0.0",
        "click >= 8.0.0, < 8.1.0",
    ],
    tests_require=[],
    entry_points={
        "console_scripts": [
            "mediacrawl = mediacrawl.cli:cli",
        ],
    },
    extras_require={
        "dev": [
            "wheel>=0.29.0",
            "twine",
            "mypy",
            "flake8>=2.6.0",
            "pytest",
            "pytest-cov",
            "coverage>=4.1",
            "types-setuptools",
            "types-requests",
        ],
    },
)
