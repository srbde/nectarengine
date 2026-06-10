from typing import Any

from nectar.instance import shared_blockchain_instance

from nectarengine.api import Api
from nectarengine.nft import Nft
from nectarengine.nfts import Nfts


class NftMarket(list):
    """Access the hive-engine NFT market

    :param Hive blockchain_instance: Hive
           instance
    """

    def __init__(self, api: Api | None = None, blockchain_instance: Any | None = None) -> None:
        if api is None:
            self.api = Api()
        else:
            self.api = api
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.nfts = Nfts(api=self.api)
        self.ssc_id = "ssc-mainnet-hive"

    def set_id(self, ssc_id: str) -> None:
        """Sets the ssc id (default is ssc-mainnet-hive)"""
        self.ssc_id = ssc_id

    def get_sell_book(
        self,
        symbol: str,
        account: str | None = None,
        grouping_name: str | None = None,
        grouping_value: str | None = None,
        priceSymbol: str | None = None,
        nftId: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Returns the sell book for a given symbol. When account is set,
        the order book from the given account is shown.
        """
        nft = Nft(symbol, api=self.api)
        query: dict[str, Any] = {}
        if account is not None:
            query["account"] = account
        if grouping_name is not None and grouping_value is not None:
            query["grouping." + grouping_name] = grouping_value
        if priceSymbol is not None:
            query["priceSymbol"] = priceSymbol.upper()
        if nftId is not None:
            query["nftId"] = nftId
        if limit is None:
            limit = -1
        sell_book = nft.get_sell_book(query=query, limit=limit)
        return sell_book

    def get_open_interest(
        self,
        symbol: str,
        side: str = "sell",
        grouping_name: str | None = None,
        grouping_value: str | None = None,
        priceSymbol: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Returns the sell book for a given symbol. When account is set,
        the order book from the given account is shown.
        """
        nft = Nft(symbol, api=self.api)
        query: dict[str, Any] = {}
        query["side"] = side
        if grouping_name is not None and grouping_value is not None:
            query["grouping." + grouping_name] = grouping_value
        if priceSymbol is not None:
            query["priceSymbol"] = priceSymbol.upper()
        if limit is None:
            limit = -1
        sell_book = nft.get_open_interest(query=query, limit=limit)
        return sell_book

    def get_trades_history(
        self,
        symbol: str,
        account: str | None = None,
        priceSymbol: str | None = None,
        timestamp: int | None = None,
    ) -> list[dict[str, Any]]:
        """Returns the trade history for a given symbol. When account is set,
        the trade history from the given account is shown.
        """
        nft = Nft(symbol, api=self.api)
        query: dict[str, Any] = {}
        if account is not None:
            query["account"] = account
        if priceSymbol is not None:
            query["priceSymbol"] = priceSymbol.upper()
        if timestamp is not None:
            query["timestamp"] = timestamp
        trades_history = nft.get_trade_history(query=query, limit=-1)
        new_trades_history: list[dict[str, Any]] = []
        last_id = None
        for trade in trades_history[::-1]:
            if last_id is None:
                last_id = trade["_id"]
            elif last_id != trade["_id"] + 1:
                continue
            else:
                last_id = trade["_id"]
            new_trades_history.append(trade)

        return new_trades_history[::-1]

    def buy(
        self, symbol: str, account: str, nft_ids: list[str] | str, market_account: str
    ) -> dict[str, Any]:
        """Buy nfts for given price.

        :param str symbol: symbol
        :param str account: account name
        :param list nft_ids: list if token ids
        :param str market_account: Account who receive the fee

        :param float price: price

        Buy example:

        .. code-block:: python

            from nectarengine.nftmarket import NftMarket
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            market = NftMarket(blockchain_instance=hive)
            market.buy("STAR", "test", ["1"], "nftmarket")
        """
        nft_list: list[str] = []
        if not isinstance(nft_ids, list):
            nft_list = [str(nft_ids)]
        else:
            for n in nft_ids:
                nft_list.append(str(n))
        contract_payload = {
            "symbol": symbol.upper(),
            "nfts": nft_list,
            "marketAccount": market_account,
        }
        json_data = {
            "contractName": "nftmarket",
            "contractAction": "buy",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def sell(
        self,
        symbol: str,
        account: str,
        nft_ids: list[str] | str,
        price: float,
        price_symbol: str,
        fee: int,
    ) -> dict[str, Any]:
        """Sell token for given price.

        :param str symbol: symbol
        :param str account: account name
        :param list nft_ids: List of nft ids
        :param float price: price
        :param str price_symbol: price symbol
        :param int fee: fee percentage (500 -> 5%)

        Sell example:

        .. code-block:: python

            from nectarengine.nftmarket import NftMarket
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            market = NftMarket(blockchain_instance=hive)
            market.sell("STAR", "test", ["1"], 100, "STARBITS", 500)

        """
        nft_list: list[str] = []
        if not isinstance(nft_ids, list):
            nft_list = [str(nft_ids)]
        else:
            for n in nft_ids:
                nft_list.append(str(n))
        contract_payload = {
            "symbol": symbol.upper(),
            "nfts": nft_list,
            "price": str(price),
            "priceSymbol": price_symbol.upper(),
            "fee": int(fee),
        }
        json_data = {
            "contractName": "nftmarket",
            "contractAction": "sell",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def change_price(
        self, symbol: str, account: str, nft_ids: list[str] | str, price: float
    ) -> dict[str, Any]:
        """Change a price for a listed nft id

        :param str symbol: nft symbol
        :param str account: account name
        :param list nft_ids: List of nfts
        :param float price: new price

        Sell example:

        .. code-block:: python

            from nectarengine.nftmarket import NftMarket
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            market = NftMarket(blockchain_instance=hive)
            market.change_price("STAR", "test", ["1"], 30)

        """

        nft_list: list[str] = []
        if not isinstance(nft_ids, list):
            nft_list = [str(nft_ids)]
        else:
            for n in nft_ids:
                nft_list.append(str(n))
        contract_payload = {"symbol": symbol.upper(), "nfts": nft_list, "price": str(price)}
        json_data = {
            "contractName": "nftmarket",
            "contractAction": "changePrice",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def cancel(self, symbol: str, account: str, nft_ids: list[str] | str) -> dict[str, Any]:
        """Cancel sell order.

        :param str symbol: symbol
        :param str account: account name
        :param list nft_ids: list of tokens ids

        Cancel example:

        .. code-block:: python

            from nectarengine.nftmarket import NftMarket
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            market = NftMarket(blockchain_instance=hive)
            market.cancel("STAR", "test", ["1"])

        """
        nft_list: list[str] = []
        if not isinstance(nft_ids, list):
            nft_list = [str(nft_ids)]
        else:
            for n in nft_ids:
                nft_list.append(str(n))
        contract_payload = {"symbol": symbol.upper(), "nfts": nft_list}
        json_data = {
            "contractName": "nftmarket",
            "contractAction": "cancel",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx
