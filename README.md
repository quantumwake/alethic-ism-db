# Alethic Instruction-Based State Machine (DB)
The following is code for processing and storing data in a database, it allows for the following functionality.
- Storage of State Information in a Database (this is a replacement of the highly problematic pickle format and also allows for centralized state management)
- Storage of State Processing into a Tabular Format in a Database


# Conda Sources
This is required to ensure that the correct pytorch is installed on Apple Silicon (MPS)

- conda config --add channels pytorch

# Dependencies

Use conda build via the build.sh script

- python-dotenv
- pyyaml
- pydantic

# Unsupported (But Planned)
Async support is not yet available, need to make some changes and add in sqlalchemy and make this database agnostic

- asyncpg (*currently not supported, need to do a lot of refactoring maybe next version)

# Initialize Conda

- conda init
- conda create -n local_channel --no-default-packages
- conda create -n alethic-ism-core python=3.11
- conda install conda-build

# Local Dependency & Build
- conda install alethic-ism-core -c ~/miniconda3/envs/local_channel
- bash build.sh

# Test
- conda install pytest
