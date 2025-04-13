# Alethic Instruction-Based State Machine (ISM) Database SDK for Python

The Alethic ISM DB (Python SDK) backend interface is an extension of [alethic-ism-core](https://github.com/quantumwake/alethic-ism-core) and provides a set of base database access functions compatibility with postgres and other backend systems.

Refer to the [Alethic ISM project group](https://github.com/quantumwake/alethic), handling the core processor and state management code. 

### Status 
This project is actively under development and remains in an experimental/prototype phase. Contributions and feedback are welcome as the project evolves.
- Postgres (crude but effective for now)
- Lots of work needs to be done on the storage subsystem to scale it up in a distributed manner

## Known issues

## Cutting a Release:

```shell
  export ISM_CORE_VERSION=v1.0.x
```

```bash
  git tag -a ${ISM_CORE_VERSION} -m "Release version ${ISM_CORE_VERSION}"
```

```bash
  git push origin ${ISM_CORE_VERSION}
```

## License
Alethic ISM is under a DUAL licensing model, please refer to [LICENSE.md](LICENSE.md).

**AGPL v3**  
Intended for academic, research, and nonprofit institutional use. As long as all derivative works are also open-sourced under the same license, you are free to use, modify, and distribute the software.

**Commercial License**
Intended for commercial use, including production deployments and proprietary applications. This license allows for closed-source derivative works and commercial distribution. Please contact us for more information.

