Changelog
=========

1.0.0
-----

- **HTTPX2**: With HTTPX itself seeing limited activity recently,
  Pydantic is picking up stewardship under the HTTPX2 name so that users
  have a reliably maintained path forward - including timely security
  updates for a library that sits in the critical path of so many
  production systems.
- **Docs**: Regenerate the Sphinx API reference from the ``src/`` layout
  so the documentation sidebar lists package modules instead of ``src``.

.. _section-1:

0.2.1
-----

- Fixed type hinting errors in ``cli.py``, ``nfts.py``, and
  ``tokenobject.py``.
- Added defensive ``None`` checks for ``nft.get_id()`` calls in CLI to
  prevent runtime errors.
- Resolved ``sys._MEIPASS`` attribute error for frozen applications.
- Refactored ``nodeslist.py`` to exclusively use PeakD Beacon API,
  removing legacy ``flowerengine`` logic.
- Added ``find_many`` to ``Api`` for efficient pagination with
  ``last_id``.
- Added ``utils.py`` with ``Query`` and ``Cond`` helpers for
  constructing queries.
- Cleaned up unused variables and imports identified by ``ruff``.

.. _section-2:

0.2.0
-----

- Migrated network layer from ``requests`` to ``httpx`` for better
  performance and modern standards.
- Enhanced ``find_all`` pagination to use ``last_id``-based recursion,
  improving reliability for large datasets.
- Silenced noisy ``httpx`` logs by default.

.. _section-3:

0.1.4
-----

- Added RPC Pool to ease use of multiple nodes, with automatic rotation
  and fallback. Uses peakd beacon, and flowerengine metadata to find
  nodes.
- Added Peakd Beacon lookup for Hive-Engine History nodes.

.. _section-4:

0.1.3
-----

- Added ``Nodes`` utility to dynamically source Hive Engine nodes from
  account metadata and expose helper methods.
- Updated ``Api`` initialization to accept node objects and sequences
  for seamless integration with node discovery.

.. _section-5:

0.1.2
-----

- Updated Docs for readthedocs release

.. _section-6:

0.1.1
-----

- Added getBlockRangeInfo to Api class

.. _section-7:

0.1.0
-----

- Fully typed codebase

.. _section-8:

0.0.9
-----

- Fixed quite a few issues with the liquidity pool and some token
  objects

.. _section-9:

0.0.8
-----

- Dropped python version down to 3.10 for compatibility

.. _section-10:

0.0.7
-----

- Replacing build system with uv

.. _section-11:

0.0.6
-----

- Removed the need for ``/`` on the end of the rpc url

.. _section-12:

0.0.5
-----

- Added Pool Object to ease use of Liquidity Pools

.. _section-13:

0.0.4
-----

- Added liquidity pool support

.. _section-14:

0.0.3
-----

- Update api test to make use of only current blocks because of
  litenodes block limits.
- Updated documentation to compile with sphinx correctly.

.. _section-15:

0.0.2
-----

- Tried to finish all the misc branding stuff that I may have missed

.. _section-16:

0.0.1
-----

- Initial version
