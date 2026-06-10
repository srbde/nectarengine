from typing import Any, Dict, List, Optional

from nectar.account import Account
from nectar.instance import shared_blockchain_instance

from nectarengine.api import Api
from nectarengine.nft import Nft
from nectarengine.nfts import Nfts


class Collection(dict):
    """Access the hive-engine NFT collection

    :param str account: Name of the account
    :param Hive blockchain_instance: Hive
           instance

    Wallet example:

        .. code-block:: python

            from nectarengine.collection import Collection
            collection = Collection("test")
            print(collection)

    """

    def __init__(
        self, account: str, api: Optional[Api] = None, blockchain_instance: Optional[Any] = None
    ) -> None:
        if api is None:
            self.api = Api()
        else:
            self.api = api
        self.ssc_id = "ssc-mainnet-hive"
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        check_account = Account(account, blockchain_instance=self.blockchain)
        self.account = check_account["name"]
        self.nfts = Nfts()
        self.refresh()

    def refresh(self) -> None:
        super().__init__(self.get_collection())

    def set_id(self, ssc_id: str) -> None:
        """Sets the ssc id (default is ssc-mainnet-hive)"""
        self.ssc_id = ssc_id

    def get_collection(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns all token within the wallet as list"""
        collection: Dict[str, List[Dict[str, Any]]] = {}
        for symbol in self.nfts.get_symbol_list():
            nft = Nft(symbol)
            tokenlist = nft.get_collection(self.account)
            if len(tokenlist) > 0:
                collection[symbol] = tokenlist
        return collection

    def change_account(self, account: str) -> None:
        """Changes the wallet account"""
        check_account = Account(account, blockchain_instance=self.blockchain)
        self.account = check_account["name"]
        self.refresh()

    def get_nft(self, nft_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Returns a token from the wallet. Is None when not available."""
        for token in self[symbol]:
            if token["_id"].lower() == nft_id:
                return token
        return None

    def transfer(
        self, to: str, nfts: List[Dict[str, Any]], from_type: str = "user", to_type: str = "user"
    ) -> Dict[str, Any]:
        """Transfer a token to another account.

        :param str to: Recipient
        :param list nfts: Amount to transfer
        :param str from_type: (optional) user / contract
        :param str to_type: (optional) user / contract


        Transfer example:

        .. code-block:: python

            from nectarengine.collection import Collection
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            collection = Collection("test", blockchain_instance=hive)
            nfts = [{"symbol": "STAR", "ids": ["100"]}]
            collection.transfer("test2", nfts)
        """
        assert from_type in ["user", "contract"]
        assert to_type in ["user", "contract"]
        assert len(nfts) > 0
        contract_payload: Dict[str, Any] = {"to": to, "nfts": nfts}
        if from_type == "contract":
            contract_payload["fromType"] = from_type
        if to_type == "contract":
            contract_payload["toType"] = to_type
        json_data = {
            "contractName": "nft",
            "contractAction": "transfer",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[self.account])
        return tx

    def burn(self, nfts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Burn a token

        :param list nfts: Amount to transfer

        Transfer example:

        .. code-block:: python

            from nectarengine.collection import Collection
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            collection = Collection("test", blockchain_instance=hive)
            nfts = [{"symbol": "STAR", "ids": ["100"]}]
            collection.burn(nfts)
        """
        assert len(nfts) > 0
        contract_payload = {"nfts": nfts}
        json_data = {
            "contractName": "nft",
            "contractAction": "burn",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[self.account])
        return tx

    def delegate(
        self, to: str, nfts: List[Dict[str, Any]], from_type: str = "user", to_type: str = "user"
    ) -> Dict[str, Any]:
        """Delegate a token to another account.

        :param str to: Recipient
        :param list nfts: Amount to transfer
        :param str from_type: (optional) user / contract
        :param str to_type: (optional) user / contract

        Transfer example:

        .. code-block:: python

            from nectarengine.collection import Collection
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            collection = Collection("test", blockchain_instance=hive)
            nfts = [{"symbol": "STAR", "ids": ["100"]}]
            collection.delegate("test2", nfts)
        """
        assert len(nfts) > 0
        assert from_type in ["user", "contract"]
        assert to_type in ["user", "contract"]
        contract_payload: Dict[str, Any] = {"to": to, "nfts": nfts}
        if from_type == "contract":
            contract_payload["fromType"] = from_type
        if to_type == "contract":
            contract_payload["toType"] = to_type
        json_data = {
            "contractName": "nft",
            "contractAction": "delegate",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[self.account])
        return tx

    def undelegate(
        self, to: str, nfts: List[Dict[str, Any]], from_type: str = "user"
    ) -> Dict[str, Any]:
        """Undelegate a token to another account.

        :param str to: Recipient
        :param list nfts: Amount to transfer
        :param str from_type: (optional) user / contract

        Transfer example:

        .. code-block:: python

            from nectarengine.collection import Collection
            from nectar import Hive
            active_wif = "5xxxx"
            hive = Hive(keys=[active_wif])
            collection = Collection("test", blockchain_instance=hive)
            nfts = [{"symbol": "STAR", "ids": ["100"]}]
            collection.undelegate("test2", nfts)
        """
        assert len(nfts) > 0
        assert from_type in ["user", "contract"]
        contract_payload: Dict[str, Any] = {"nfts": nfts}
        if from_type == "contract":
            contract_payload["fromType"] = from_type
        json_data = {
            "contractName": "nft",
            "contractAction": "undelegate",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[self.account])
        return tx
