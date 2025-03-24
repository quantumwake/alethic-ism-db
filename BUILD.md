# Requirements
* `pip install uv`

# Environment
* `uv venv`
* `source .venv/bin/activate`

# Build package 
* `uv pip install -U pip setuptools build`
* `uv pip install -e .`
* `python -m build`

# Alethic Dependencies

* Directly via local whl
  * `uv pip install ../alethic-ism-core/dist/alethic_ism_core-1.0.0-py3-none-any.wh`


* OR (if you want live edits to propagate)
  * `uv pip install -e ../alethic-ism-core/`

# Other (TBD)
* `uv pip install --find-links`