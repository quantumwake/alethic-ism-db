from setuptools import setup, find_packages

setup(
    name="alethic-ism-db",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    url="https://github.com/quantumwake/alethic-ism-db",
    license="AGPL-3.0-or-later",  # Updated to AGPL
    author="Kasra Rasaee",
    author_email="krasaee@quantumwake.io",
    description="Alethic Instruction-Based State Machine (DB Python SDK)",
    classifiers=[
         "Programming Language :: Python :: 3",
         "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
