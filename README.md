# Alethic Instruction-Based State Machine (DB Module)
The Alethic ISM DB (Python) backend interface is an extension of [alethic-ism-core](https://github.com/quantumwake/alethic-ism-core) and provides a set of base database access functions compatibility with postgres and other backend systems.

- Database access functionality for the Alethic ISM models, including the State and other Functions of the ISM platform, the system as a whole.
- Warning: this is a work in progress and is a crude implementation of a storage subsystem for the Alethic ISM platform (for python users). However, it works well enough for now.

## Current Support
- Postgres (crude but effective for now)
- Lots of work needs to be done on the storage subsystem to scale it up in a distributed manner

## Initialize Conda
Create a new conda environment

```bash
conda install -y conda-build anaconda-client -c conda-forge --override-channels
```
```bash
conda env create -f environment.yaml
```

## Acknowledgements
Alethic Research, Princeton University Center for Human Values, New York University

## Known issues
Update conda base version to fix warnings and potentially other issues related to outdated conda binaries.

```bash
conda update -n base -c defaults conda
```

**Error while loading conda entry point: conda-libmamba-solver** (No module named 'libmambapy') 
 This is a known issue with conda and can be resolved by running the following command:

```bash
conda install -n base -c conda-forge libmambapy --force-reinstall
```
```bash
conda install -n base -c conda-forge libmamba --force-reinstall
```
```bash
conda install -n base -c conda-forge mamba --force-reinstall
```

# License
Alethic ISM and all its components is made available under a dual licensing model by quantumwake.io.

- **Open Source License:**  
  For community and open source use, the project is released under the [GNU General Public License v3 (GPLv3)](LICENSE). This license ensures that any modifications or derivative works distributed to the public remain open and free under the same terms.

- **Commercial License:**  
  If you prefer to use Alethic ISM or any of its components in a proprietary or closed-source product without the obligations of the GPLv3, a commercial license is available. Please review our [Dual Licensing Agreement](DUAL_LICENSE.md) for details or contact us directly.

For more information or licensing inquiries, please visit [https://quantumwake.io](https://quantumwake.io) or email us at [licensing@quantumwake.io](mailto:licensing@quantumwake.io).
