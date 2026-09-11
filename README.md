# mcontrol

`mcontrol` is a command-line tool for creating, starting, and stopping local MongoDB deployments for development and testing. It automates the setup of standalone replica sets and sharded clusters by generating configuration files and managing `mongod`/`mongos` process lifecycles.

## Prerequisites

- Python 3.6+
- `mongod` (and `mongos` for sharded clusters) on `$PATH`
- `openssl` on `$PATH`

## Installation

### Development install (editable)

Use this if you plan to modify the source code. Changes take effect immediately without reinstalling.

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and the package in editable mode
pip install -r requirements.txt
pip install -e .
```

### Standard install

Use this for a regular installation from source.

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install .
```

### Install from a built package

Build a distributable egg and install it.

```bash
python3 -m venv .venv
source .venv/bin/activate

python setup.py bdist_egg
pip install dist/mcontrol-*.egg
```

After installation the `mcontrol` command is available in your shell.

> **Note:** All commands must be run from the directory where you want the deployment to live. A `data/` subdirectory will be created there to hold all configs, data files, logs, and PID files.

## Usage

### `init` — Create and start a new cluster

Generates configuration files, starts all processes, and initializes replica sets (and shards, if applicable).

```
mcontrol [--debug] init [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--shards N` | int | `0` | Number of shards. `0` = replica set, `>0` = sharded cluster |
| `--nodes N` | int | `3` | Number of nodes per replica set |
| `--arbiters N` | int | `0` | Number of arbiter nodes (counted within `--nodes`) |
| `--replSetName NAME` | str | `rs` | Replica set name (replica sets only) |
| `--startPort PORT` | int | `27017` | Starting port for the deployment |
| `--auth` | bool | `True` | Enable keyfile authentication |

### `start` — Resume a stopped cluster

Reads the saved cluster configuration from `data/mcontrol.yml` and starts all processes.

```
mcontrol [--debug] start
```

### `stop` — Stop a running cluster

Stops all running `mongod`/`mongos` processes belonging to the current deployment.

```
mcontrol [--debug] stop
```

### `--debug`

Global flag that enables verbose debug-level logging. Can be used with any command.

```
mcontrol --debug init --shards 2
```

## Examples

### Replica Set

**Default 3-node replica set** on port 27017 with authentication:

```bash
mcontrol init
```

**Custom replica set name and starting port:**

```bash
mcontrol init --replSetName myRS --startPort 28000
```

**5-node replica set with 1 arbiter:**

```bash
mcontrol init --nodes 5 --arbiters 1
```

**Replica set without authentication:**

```bash
mcontrol init --auth false
```

**Connect after init (auth enabled):**

```
mongodb://admin:password@localhost:27017/?replicaSet=rs
```

**Stop and restart the cluster:**

```bash
mcontrol stop
mcontrol start
```

---

### Sharded Cluster

**2-shard cluster** (3 nodes per shard, default ports):

```bash
mcontrol init --shards 2
```

**3-shard cluster with 1 arbiter per shard:**

```bash
mcontrol init --shards 3 --nodes 3 --arbiters 1
```

**2-shard cluster with a custom mongos port:**

```bash
mcontrol init --shards 2 --startPort 28000
```

**Connect after init** (via mongos, auth enabled):

```
mongodb://admin:password@localhost:27017/
```

**Stop and restart the cluster:**

```bash
mcontrol stop
mcontrol start
```

## Notes

- **Default credentials** (when `--auth` is enabled): username `admin`, password `password`.
- **Port layout for sharded clusters:**
  - `mongos`: `startPort` (default `27017`)
  - Config servers: `27018`, `27019`, `27020` (always 3 nodes, replica set named `configRS`)
  - Shard nodes: `27030+` — shard 0 starts at `27030`, shard 1 at `27033`, and so on
- **Paths are absolute and baked in at `init` time.** Do not move the `data/` directory after initialization — use `stop`, delete `data/`, and run `init` again if you need to relocate.
- The config server replica set is always 3 nodes on ports `27018`–`27020` and is not configurable via CLI flags.

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
