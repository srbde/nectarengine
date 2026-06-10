from typing import Any, Dict, List, Optional

from nectarengine.api import Api
from nectarengine.tokenobject import Token


class Tokens(list):
    """Access the hive-engine tokens"""

    def __init__(self, api: Optional[Api] = None, **kwargs: Any) -> None:
        if api is None:
            self.api = Api()
        else:
            self.api = api
        self.refresh()

    def refresh(self) -> None:
        super().__init__(self.get_token_list())

    def get_token_list(self) -> List[Dict[str, Any]]:
        """Returns all available token as list"""
        tokens = self.api.find_all("tokens", "tokens", query={})
        return tokens

    def get_token(self, symbol: str) -> Optional[Token]:
        """Returns Token from given token symbol. Is None
        when token does not exists.
        """
        for t in self:
            if t["symbol"].lower() == symbol.lower():
                return Token(t, api=self.api)
        return None
