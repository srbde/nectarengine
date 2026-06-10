import decimal
from typing import Any, Dict, List, Optional, Union

from nectarengine.api import Api
from nectarengine.exceptions import TokenDoesNotExists


class Token(dict):
    """hive-engine token dict

    :param str token: Name of the token
    """

    def __init__(self, symbol: Union[str, Dict[str, Any]], api: Optional[Api] = None) -> None:
        if api is None:
            self.api = Api()
        else:
            self.api = api
        if isinstance(symbol, dict):
            self.symbol = symbol["symbol"]
            super().__init__(symbol)
        else:
            self.symbol = symbol.upper()
            self.refresh()

    def refresh(self) -> None:
        info = self.get_info()
        if info is None:
            raise TokenDoesNotExists("Token %s does not exists!" % self.symbol)
        super().__init__(info)

    def quantize(self, amount: Union[float, int, str]) -> decimal.Decimal:
        """Round down a amount using the token precision and returns a Decimal object"""
        decimal_amount = decimal.Decimal(amount)
        places = decimal.Decimal(10) ** (-self["precision"])
        return decimal_amount.quantize(places, rounding=decimal.ROUND_DOWN)

    def get_info(self) -> Optional[Dict[str, Any]]:
        """Returns information about the token"""
        # self.api.find_one now returns the token dictionary directly if found, or None otherwise.
        token_data = self.api.find_one("tokens", "tokens", query={"symbol": self.symbol})
        return token_data

    def get_holder(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Returns all token holders"""
        holder = self.api.find(
            "tokens",
            "balances",
            query={"symbol": self.symbol},
            limit=limit,
            offset=offset,
        )
        return holder

    def get_all_holder(self) -> List[Dict[str, Any]]:
        """Returns all token holders by looping through all pages"""
        return self.api.find_all("tokens", "balances", query={"symbol": self.symbol})

    def get_market_info(self) -> Optional[Dict[str, Any]]:
        """Returns market information"""
        metrics = self.api.find_one("market", "metrics", query={"symbol": self.symbol})
        if metrics and isinstance(metrics, list) and len(metrics) > 0:
            return metrics[0]
        elif metrics and isinstance(metrics, dict):
            return metrics
        else:
            return None

    def get_buy_book(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Returns the buy book"""
        holder = self.api.find(
            "market",
            "buyBook",
            query={"symbol": self.symbol},
            limit=limit,
            offset=offset,
        )
        return holder

    def get_all_buy_book(self) -> List[Dict[str, Any]]:
        """Returns the buy book by looping through all pages"""
        return self.api.find_all("market", "buyBook", query={"symbol": self.symbol})

    def get_sell_book(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Returns the sell book"""
        holder = self.api.find(
            "market",
            "sellBook",
            query={"symbol": self.symbol},
            limit=limit,
            offset=offset,
        )
        return holder

    def get_all_sell_book(self) -> List[Dict[str, Any]]:
        """Returns the sell book by looping through all pages"""
        return self.api.find_all("market", "sellBook", query={"symbol": self.symbol})
