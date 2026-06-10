import decimal
import logging
from typing import Any, Dict, List, Optional

# Third-party imports
from nectar.instance import shared_blockchain_instance

# Local application imports
from nectarengine.api import Api
from nectarengine.exceptions import (
    InsufficientTokenAmount,
    InvalidTokenAmount,
    PoolDoesNotExist,
    TokenNotInWallet,
)
from nectarengine.poolobject import Pool
from nectarengine.tokenobject import Token
from nectarengine.tokens import Tokens
from nectarengine.wallet import Wallet

log = logging.getLogger(__name__)


class LiquidityPool(list):
    """Access the hive-engine liquidity pools

    :param Hive blockchain_instance: Hive
           instance
    """

    def __init__(
        self, api: Optional[Api] = None, blockchain_instance: Optional[Any] = None
    ) -> None:
        if api is None:
            self.api = Api()
        else:
            self.api = api
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.tokens = Tokens(api=self.api)
        self.ssc_id = "ssc-mainnet-hive"
        self.refresh()

    def refresh(self) -> None:
        super().__init__(self.get_pools())

    def set_id(self, ssc_id: str) -> None:
        """Sets the ssc id (default is ssc-mainnet-hive)"""
        self.ssc_id = ssc_id

    def get_pools(self) -> List[Dict[str, Any]]:
        """Returns all liquidity pools as list"""
        pools = self.api.find("marketpools", "pools", query={})
        return pools

    def get_pool(self, token_pair: str) -> Pool:
        """Returns a specific liquidity pool for a given token pair

        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'
        :raises PoolDoesNotExist: If the pool does not exist
        :return: Pool object
        :rtype: Pool
        """
        try:
            return Pool(token_pair, api=self.api)
        except PoolDoesNotExist:
            raise PoolDoesNotExist(token_pair)

    def get_liquidity_positions(
        self,
        account: Optional[str] = None,
        token_pair: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Returns liquidity positions. When account is set,
        only positions from the given account are shown. When token_pair is set,
        only positions for the given token pair are shown.
        """
        query: Dict[str, Any] = {}
        if account is not None:
            query["account"] = account
        if token_pair is not None:
            query["tokenPair"] = token_pair.upper()

        positions = self.api.find(
            "marketpools", "liquidityPositions", query=query, limit=limit, offset=offset
        )
        return positions

    def create_pool(self, account: str, token_pair: str) -> Dict[str, Any]:
        """Create a new liquidity pool for a token pair.

        :param str account: account name
        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'

        Create pool example:

        .. code-block:: python

            from nectarengine.pool import LiquidityPool
            from nectar import Hive
            active_wif = "5xxxx"
            hv = Hive(keys=[active_wif])
            pool = LiquidityPool(blockchain_instance=hv)
            pool.create_pool("test", "GLD:SLV")
        """
        contract_payload = {"tokenPair": token_pair.upper()}
        json_data = {
            "contractName": "marketpools",
            "contractAction": "createPool",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def swap_tokens(
        self,
        account: str,
        token_pair: str,
        token_symbol: str,
        token_amount: float,
        trade_type: str,
        min_amount_out: Optional[float] = None,
        max_amount_in: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Swap tokens using a liquidity pool.

        :param str account: account name
        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'
        :param str token_symbol: Token symbol being traded
        :param float token_amount: Amount of tokens to trade
        :param str trade_type: Either 'exactInput' or 'exactOutput'
        :param float min_amount_out: (optional) Minimum amount expected out for exactInput trade
        :param float max_amount_in: (optional) Maximum amount expected in for exactOutput trade

        Swap tokens example (exactInput):

        .. code-block:: python

            from nectarengine.pool import LiquidityPool
            from nectar import Hive
            active_wif = "5xxxx"
            hv = Hive(keys=[active_wif])
            pool = LiquidityPool(blockchain_instance=hv)
            pool.swap_tokens("test", "GLD:SLV", "GLD", 1, "exactInput", min_amount_out=1)
        """
        wallet = Wallet(account, api=self.api, blockchain_instance=self.blockchain)
        token_in_wallet = wallet.get_token(token_symbol)
        if token_in_wallet is None:
            raise TokenNotInWallet("%s is not in wallet." % token_symbol)

        if trade_type == "exactInput" and float(token_in_wallet["balance"]) < float(token_amount):
            raise InsufficientTokenAmount("Only %.3f in wallet" % float(token_in_wallet["balance"]))

        token = Token(token_symbol, api=self.api)
        quant_amount = token.quantize(token_amount)
        if quant_amount <= decimal.Decimal("0"):
            raise InvalidTokenAmount(
                "Amount to transfer is below token precision of %d" % token["precision"]
            )

        contract_payload: Dict[str, Any] = {
            "tokenPair": token_pair.upper(),
            "tokenSymbol": token_symbol.upper(),
            "tokenAmount": str(quant_amount),
            "tradeType": trade_type,
        }

        if min_amount_out is not None and trade_type == "exactInput":
            # Determine output token symbol
            base_sym, quote_sym = token_pair.upper().split(":")
            output_token_symbol = base_sym if token_symbol.upper() == quote_sym else quote_sym

            # Get precision of the output token
            output_token_details = self.tokens.get_token(output_token_symbol)
            if not output_token_details:
                # This should ideally not happen if the pool and tokens are valid
                raise ValueError(
                    f"Could not get details for output token {output_token_symbol} to determine precision for minAmountOut."
                )
            # Assuming output_token_details is a Token object or dict-like with 'precision'
            output_precision = output_token_details["precision"]

            # Ensure min_amount_out is a Decimal, then format it
            try:
                min_amount_out_decimal = decimal.Decimal(
                    str(min_amount_out)
                )  # Convert to string first for robust Decimal conversion
            except decimal.InvalidOperation:
                raise InvalidTokenAmount(
                    f"min_amount_out '{min_amount_out}' is not a valid number."
                )

            quantizer = decimal.Decimal(f"1e-{output_precision}")
            formatted_min_amount_out = str(
                min_amount_out_decimal.quantize(quantizer, rounding=decimal.ROUND_DOWN)
            )
            contract_payload["minAmountOut"] = formatted_min_amount_out
        if max_amount_in is not None and trade_type == "exactOutput":
            contract_payload["maxAmountIn"] = str(max_amount_in)

        json_data = {
            "contractName": "marketpools",
            "contractAction": "swapTokens",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def add_liquidity(
        self,
        account: str,
        token_pair: str,
        base_quantity: float,
        quote_quantity: float,
        max_price_impact: Optional[float] = None,
        max_deviation: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Add liquidity to a pool.

        :param str account: account name
        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'
        :param float base_quantity: Amount to deposit into the base token reserve (first token in pair)
        :param float quote_quantity: Amount to deposit into the quote token reserve (second token in pair)
        :param float max_price_impact: (optional) Amount of tolerance to price impact after adding liquidity
        :param float max_deviation: (optional) Amount of tolerance to price difference versus the regular HE market

        Add liquidity example:

        .. code-block:: python

            from nectarengine.pool import LiquidityPool
            from nectar import Hive
            active_wif = "5xxxx"
            hv = Hive(keys=[active_wif])
            pool = LiquidityPool(blockchain_instance=hv)
            pool.add_liquidity("test", "GLD:SLV", 1000, 16000, max_price_impact=1, max_deviation=1)
        """
        tokens = token_pair.upper().split(":")
        if len(tokens) != 2:
            raise ValueError("Token pair must be in the format 'TOKEN1:TOKEN2'")

        base_token = tokens[0]
        quote_token = tokens[1]

        wallet = Wallet(account, api=self.api, blockchain_instance=self.blockchain)
        base_token_in_wallet = wallet.get_token(base_token)
        quote_token_in_wallet = wallet.get_token(quote_token)

        if base_token_in_wallet is None:
            raise TokenNotInWallet("%s is not in wallet." % base_token)
        if quote_token_in_wallet is None:
            raise TokenNotInWallet("%s is not in wallet." % quote_token)

        if float(base_token_in_wallet["balance"]) < float(base_quantity):
            raise InsufficientTokenAmount(
                f"Only {float(base_token_in_wallet['balance']):.3f} {base_token} in wallet"
            )
        if float(quote_token_in_wallet["balance"]) < float(quote_quantity):
            raise InsufficientTokenAmount(
                f"Only {float(quote_token_in_wallet['balance']):.3f} {quote_token} in wallet"
            )

        contract_payload: Dict[str, Any] = {
            "tokenPair": token_pair.upper(),
            "baseQuantity": str(base_quantity),
            "quoteQuantity": str(quote_quantity),
        }

        if max_price_impact is not None:
            contract_payload["maxPriceImpact"] = str(max_price_impact)
        if max_deviation is not None:
            contract_payload["maxDeviation"] = str(max_deviation)

        json_data = {
            "contractName": "marketpools",
            "contractAction": "addLiquidity",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def remove_liquidity(self, account: str, token_pair: str, shares_out: float) -> Dict[str, Any]:
        """Remove liquidity from a pool.

        :param str account: account name
        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'
        :param float shares_out: Percentage > 0 <= 100 - amount of liquidity shares to convert into tokens

        Remove liquidity example:

        .. code-block:: python

            from nectarengine.pool import LiquidityPool
            from nectar import Hive
            active_wif = "5xxxx"
            hv = Hive(keys=[active_wif])
            pool = LiquidityPool(blockchain_instance=hv)
            pool.remove_liquidity("test", "GLD:SLV", 50)
        """
        if float(shares_out) <= 0 or float(shares_out) > 100:
            raise ValueError("shares_out must be a percentage > 0 and <= 100")

        contract_payload = {
            "tokenPair": token_pair.upper(),
            "sharesOut": str(shares_out),
        }

        json_data = {
            "contractName": "marketpools",
            "contractAction": "removeLiquidity",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def create_reward_pool(
        self,
        account: str,
        token_pair: str,
        lottery_winners: int,
        lottery_interval_hours: int,
        lottery_amount: float,
        mined_token: str,
    ) -> Dict[str, Any]:
        """Create a reward pool for liquidity providers.

        :param str account: account name
        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'
        :param int lottery_winners: Number of lottery winners per round (1-20)
        :param int lottery_interval_hours: How often in hours to run a lottery (1-720)
        :param float lottery_amount: Amount to pay out per round
        :param str mined_token: Which token to issue as reward

        Create reward pool example:

        .. code-block:: python

            from nectarengine.pool import LiquidityPool
            from nectar import Hive
            active_wif = "5xxxx"
            hv = Hive(keys=[active_wif])
            pool = LiquidityPool(blockchain_instance=hv)
            pool.create_reward_pool("test", "GLD:SLV", 20, 1, 1, "GLD")
        """
        if lottery_winners < 1 or lottery_winners > 20:
            raise ValueError("lottery_winners must be between 1 and 20")
        if lottery_interval_hours < 1 or lottery_interval_hours > 720:
            raise ValueError("lottery_interval_hours must be between 1 and 720")

        contract_payload = {
            "tokenPair": token_pair.upper(),
            "lotteryWinners": lottery_winners,
            "lotteryIntervalHours": lottery_interval_hours,
            "lotteryAmount": str(lottery_amount),
            "minedToken": mined_token.upper(),
        }

        json_data = {
            "contractName": "marketpools",
            "contractAction": "createRewardPool",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx

    def set_reward_pool_active(
        self, account: str, token_pair: str, mined_token: str, active: bool
    ) -> Dict[str, Any]:
        """Enable or disable a reward pool.

        :param str account: account name
        :param str token_pair: Token pair in the format 'TOKEN1:TOKEN2'
        :param str mined_token: Which token to issue as reward
        :param bool active: Set reward pool to active or inactive

        Set reward pool active example:

        .. code-block:: python

            from nectarengine.pool import LiquidityPool
            from nectar import Hive
            active_wif = "5xxxx"
            hv = Hive(keys=[active_wif])
            pool = LiquidityPool(blockchain_instance=hv)
            pool.set_reward_pool_active("test", "GLD:SLV", "GLD", True)
        """
        contract_payload = {
            "tokenPair": token_pair.upper(),
            "minedToken": mined_token.upper(),
            "active": active,
        }

        json_data = {
            "contractName": "marketpools",
            "contractAction": "setRewardPoolActive",
            "contractPayload": contract_payload,
        }
        assert self.blockchain.is_hive
        tx = self.blockchain.custom_json(self.ssc_id, json_data, required_auths=[account])
        return tx
