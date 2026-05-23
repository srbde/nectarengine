Quickstart
==========

Hive Engine API
---------------

The core of nectarengine is the ``Api`` class, which provides access to the Hive Engine sidechain data.

.. code-block:: python

   from nectarengine.api import Api
   api = Api()
   
   # Get the latest block
   print(api.get_latest_block_info())
   
   # Get a specific block
   print(api.get_block_info(1910))
   
   # Get a transaction
   print(api.get_transaction_info("e6c7f351b3743d1ed3d66eb9c6f2c102020aaa5d"))
   
   # Get history for an account and token
   print(api.get_history("test_user", "BEE"))

Wallet and Token Operations
---------------------------

To perform operations like transfers, you need a ``Wallet`` instance and a ``Hive`` connection from the ``Nectar`` library.

.. code-block:: python

   from nectar import Hive
   from nectarengine.wallet import Wallet
   
   # Initialize Hive with your active key
   hive = Hive(keys=["your-active-private-key"])
   
   # Create a wallet for your account
   wallet = Wallet("youraccount", blockchain_instance=hive)
   
   # Transfer tokens
   wallet.transfer("recipient", 1.0, "BEE", memo="Quickstart transfer")

Market Operations
-----------------

The ``Market`` class allows you to interact with the Hive Engine DEX.

.. code-block:: python

   from nectar import Hive
   from nectarengine.market import Market
   
   hive = Hive(keys=["your-active-private-key"])
   market = Market(blockchain_instance=hive)
   
   # Place a buy order
   market.buy("youraccount", 100, "SWAP.HIVE", 0.5)
   
   # Place a sell order
   market.sell("youraccount", 100, "SWAP.HIVE", 0.6)
   
   # Cancel an order
   open_orders = market.get_buy_book("SWAP.HIVE", "youraccount")
   if open_orders:
       market.cancel("youraccount", "buy", open_orders[0]["_id"])

NFT Operations
--------------

``nectarengine`` also supports NFT operations on Hive Engine.

.. code-block:: python

   from nectar import Hive
   from nectarengine.nft import Nft
   
   hive = Hive(keys=["your-active-private-key"])
   nft = Nft(blockchain_instance=hive)
   
   # Transfer an NFT
   nft.transfer("youraccount", "recipient", "NFT_SYMBOL", [123], memo="Sending NFT")
