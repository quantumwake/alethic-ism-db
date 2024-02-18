# Alethic Instruction-Based State Machine (DB)
The Alethic ISM Database Interface enhances the Alethic ISM project by introducing database storage for state information as a flexible alternative to the traditional file-based system. It is tailored for compatibility with postgres and other database systems (but we can also use a DHT for more flexibility), streamlining the capture of state updates from any one or more ISM processor implementation. This design strengthens the support of a centralized data management but also facilitates distributed environments, where multiple processors can seamlessly access and utilize the same state data, thereby streamlining instruction execution and improving system efficiency and performance.

## High-level functionality:
- Storage of State information in a Database (this is a replacement of the highly problematic pickle format and also allows for centralized state management)
- Storage of State Processing into a Tabular Format in a Database
- Base Database State Storage Processor that can be inherited to perform language based instructions.
- Base classes to create other state storage options (e.g. Redis or external cache)

## Conda Sources
This is required to ensure that the correct pytorch is installed on Apple Silicon (MPS)

- conda config --add channels pytorch

## Dependencies

Use conda build via the build.sh script

- python-dotenv
- pyyaml
- pydantic

## Unsupported (But Planned)
Async support is not yet available, need to make some changes and add in sqlalchemy and make this database agnostic

- asyncpg (*currently not supported, need to do a lot of refactoring maybe next version)

## Initialize Conda

- conda init
- conda create -n local_channel --no-default-packages
- conda create -n alethic-ism-core python=3.11
- conda install conda-build

## Local Dependency & Build
- conda install alethic-ism-core -c ~/miniconda3/envs/local_channel
- bash build.sh

## Test
- conda install pytest

## Contribution
We warmly welcome contributions, questions, and feedback. Feel free to reach out if you have any queries or suggestions for the project.

## License
The Alethic ISM is released under the AGPL/GNU3 license.

## Acknowledgements
Alethic Research, Princeton University Center for Human Values, New York University
