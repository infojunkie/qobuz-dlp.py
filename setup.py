from setuptools import setup, find_packages

pkg_name = "qobuz-dlp"


def read_file(fname):
    with open(fname, "r") as f:
        return f.read()


requirements = [
    "pathvalidate",
    "requests",
    "mutagen",
    "tqdm",
    "pick==1.6.0",
    "beautifulsoup4",
    "colorama",
]

setup(
    name=pkg_name,
    version="0.11.0",
    author="infojunkie",
    author_email="karim.ratib@gmail.com",
    description="The complete lossless and hi-res music downloader for Qobuz.",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/infojunkie/qobuz-dlp",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "qobuz-dlp = qobuz_dl:main",
        ],
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

# rm -f dist/*
# python3 setup.py sdist bdist_wheel
# twine upload dist/*
