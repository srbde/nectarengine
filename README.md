# 🐝 nectarengine

**The modern Python library for Hive Engine tokens. Built for production. Made to last.**

`nectarengine` is the high-performance companion to [Nectar](https://github.com/srbde/hive-nectar), specifically designed for interacting with the Hive Engine sidechain. While Nectar handles the core blockchain layer, `nectarengine` provides an opinionated, resilient, and simplified interface for token operations, market trading, and NFT management.

If you are building on Hive Engine, `nectarengine` is the tool you need.

---

[![PyPI version](https://img.shields.io/pypi/v/nectarengine.svg)](https://pypi.python.org/pypi/nectarengine/)
[![Python Versions](https://img.shields.io/pypi/pyversions/nectarengine.svg)](https://pypi.python.org/pypi/nectarengine/)
[![License](https://img.shields.io/github/license/srbde/nectarengine.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://nectarengine.readthedocs.io)

---

## Why nectarengine?

Three ways `nectarengine` simplifies sidechain development.

### ⚡ Built on Nectar

`nectarengine` is built on top of [Nectar](https://github.com/srbde/hive-nectar), inheriting its modern cryptography, connection pooling, and resilient transport layers. It replaces legacy sidechain tools with a clean, typed API.

### 🐳 Container-Native & Serverless Ready

Inheriting Nectar's philosophy, `nectarengine` is designed to run anywhere. It handles environment-specific challenges—like read-only filesystems in Docker or Kubernetes—by defaulting to in-memory fallbacks when local storage is unavailable.

### 🪙 Unified Sidechain Interface

Forget complex JSON-RPC calls. `nectarengine` provides dedicated objects for:

- **Tokens**: Easy balance checks, transfers, and metadata lookups.
- **Market**: Seamless buy/sell orders and order book management.
- **NFTs**: Comprehensive support for minting, transferring, and querying digital assets.

---

## 🚀 Quick Start

Requires Python >= 3.10.

```bash
pip install nectarengine
```

### Get sidechain status

```python
from nectarengine.api import Api

api = Api()
print(f"Latest Block: {api.get_latest_block_info()['blockNumber']}")
```

### Send Tokens

```python
from nectar import Hive
from nectarengine.wallet import Wallet

# Initialize Hive with your active key
hive = Hive(keys=["your-active-private-key"])

# Create a wallet for the account
wallet = Wallet("youraccount", blockchain_instance=hive)

# Transfer 1.0 BEE to a recipient
wallet.transfer("recipient", 1.0, "BEE", memo="Sent with nectarengine")
```

### Trade on the Market

```python
from nectar import Hive
from nectarengine.market import Market

hive = Hive(keys=["your-active-private-key"])
market = Market(blockchain_instance=hive)

# Buy 100 SWAP.HIVE with BEE at a price of 0.5
market.buy("youraccount", 100, "SWAP.HIVE", 0.5)
```

---

## 🛠️ System Prerequisites

On platforms where binary wheels for `coincurve` and `cryptography` are not precompiled, build tools are required to compile the C extensions.

### Debian / Ubuntu

```bash
sudo apt-get install build-essential libssl-dev python3-dev python3-pip libffi-dev libtool autoconf automake pkg-config
```

### Fedora / RHEL

```bash
sudo dnf install gcc openssl-devel python3-devel libffi-devel libtool autoconf automake pkgconfig
```

---

## 🌐 Built by SRBDE

`nectarengine` is developed and maintained by the **Sustainable Resource and Business Development Enterprise (SRBDE)** — an open-source infrastructure organization building tools and platforms for communities that build things together.

We apply the logic of agricultural sustainability to software: the goal is always to return more to the ecosystem than we extract.

- **Open source is our value, not just our business model.**
- **Our commercial products fund our open-source core. The open work is the mission.**

### Explore the Ecosystem

| Project                                               | Description                       |
| ----------------------------------------------------- | --------------------------------- |
| [Pollen](https://github.com/srbde/pollen)             | The modern Hive TypeScript SDK    |
| [Anther](https://github.com/srbde/anther)             | The modern Hive Go SDK            |
| [Xylem](https://github.com/srbde/xylem)               | The modern Hive Rust SDK          |
| [Nectar](https://github.com/srbde/hive-nectar)        | The modern Hive Python SDK        |
| [nectarengine](https://github.com/srbde/nectarengine) | The Hive-Engine sidechain library |
| [ecoinstats.net](https://ecoinstats.net)              | SRBDE corporate hub               |
| [thecrazygm.com](https://thecrazygm.com)              | Open gaming tools & TTRPGs        |

---

## 🤝 Contributing

Audits, forks, and pull requests are welcome. If you find a security issue, please open a private advisory rather than a public issue.
