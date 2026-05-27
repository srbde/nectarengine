Welcome to nectarengine's documentation!
========================================

Hive Engine is a smart contracts platform on top of the Hive blockchain. It
allows for the creation and management of custom tokens, NFTs, and markets.

nectarengine is a Python library built on top of `Nectar <https://github.com/srbde/hive-nectar>`_
that simplifies interacting with the Hive Engine sidechain. It provides
a clean, resilient interface for token operations, market trading, and NFT management.

About this Library
------------------

The purpose of *nectarengine* is to simplify development of products and
services that use Hive Engine. It comes with:

* RPC interface for the Hive Engine sidechain backend
* Dedicated objects for Tokens, NFTs, and Markets
* Simplified wallet management for sidechain operations
* Transaction construction and signing for Hive Engine contracts
* *and more*

Quickstart
----------

.. code-block:: python

   from nectarengine.api import Api
   api = Api()
   print(api.get_latest_block_info())

.. code-block:: python

   from nectar import Hive
   from nectarengine.wallet import Wallet
   hive = Hive(keys=["your-active-key"])
   wallet = Wallet("test_user", blockchain_instance=hive)
   wallet.transfer("recipient", 1, "BEE", memo="This is a test")

General
-------
.. toctree::
   :maxdepth: 1

   installation
   quickstart
   changelog
   tutorials
   cli
   modules
   contribute
   support
   indices



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
