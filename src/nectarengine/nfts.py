from typing import Any

from nectarengine.api import Api
from nectarengine.nft import Nft


class Nfts(list):
    """Access the Hive-engine Nfts"""

    def __init__(self, api: Api | None = None, **kwargs: Any) -> None:
        if api is None:
            self.api = Api()
        else:
            self.api = api
        self.refresh()

    def refresh(self) -> None:
        super().__init__(self.get_nft_list())

    def get_nft_list(self) -> list[dict[str, Any]]:
        """Returns all available nft as list"""
        tokens = self.api.find_all("nft", "nfts", query={})
        return tokens

    def get_nft_params(self) -> dict[str, Any] | None:
        """Returns NFT parameters as a dictionary, or None if not found"""
        tokens = self.api.find_one("nft", "params", query={})
        if isinstance(tokens, list):
            if len(tokens) > 0:
                return tokens[0]
            return None
        if isinstance(tokens, dict):
            return tokens
        return None

    def get_symbol_list(self) -> list[str]:
        symbols: list[str] = []
        for nft in self:
            symbols.append(nft["symbol"])
        return symbols

    def get_nft(self, nft: str) -> Nft | None:
        """Returns Token from given nft symbol. Is None
        when nft does not exists.
        """
        for t in self:
            if t["symbol"].lower() == nft.lower():
                return Nft(t, api=self.api)
        return None
