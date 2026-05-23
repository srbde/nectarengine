import pytest

from nectarengine.exceptions import PoolDoesNotExist
from nectarengine.pool import LiquidityPool
from nectarengine.poolobject import Pool


@pytest.fixture
def liquidity_pool():
    return LiquidityPool()


@pytest.fixture
def test_pool(liquidity_pool):
    return liquidity_pool.get_pool("ARCHON:SWAP.HIVE")


def test_get_pool(liquidity_pool):
    # Test getting an existing pool
    pool = liquidity_pool.get_pool("ARCHON:SWAP.HIVE")
    assert isinstance(pool, Pool)
    assert pool["tokenPair"] == "ARCHON:SWAP.HIVE"

    # Test getting a non-existent pool
    with pytest.raises(PoolDoesNotExist):
        liquidity_pool.get_pool("NON:EXISTENT")


def test_pool_info(test_pool):
    # Test basic pool information
    info = test_pool.get_info()
    assert isinstance(info, dict)
    assert "tokenPair" in info
    assert "baseQuantity" in info
    assert "quoteQuantity" in info


def test_liquidity_positions(test_pool):
    # Test getting liquidity positions
    positions = test_pool.get_liquidity_positions()
    assert isinstance(positions, list)
    if positions:  # If there are positions
        assert "account" in positions[0]
        assert "shares" in positions[0]


def test_calculate_tokens_out(test_pool):
    # Test token calculations
    tokens = test_pool.get_tokens()
    token_in = tokens[0]
    tokens[1]

    # Test valid calculation
    amount_out = test_pool.calculate_tokens_out(token_in, "1.0")
    assert isinstance(amount_out, str)

    # Test invalid token
    with pytest.raises(ValueError):
        test_pool.calculate_tokens_out("INVALID", "1.0")

    # Test insufficient liquidity
    with pytest.raises(ValueError):
        test_pool.calculate_tokens_out(token_in, "9999999999999999")


def test_calculate_tokens_in(test_pool):
    # Test token calculations
    tokens = test_pool.get_tokens()
    tokens[0]
    token_out = tokens[1]

    # Test valid calculation
    amount_in = test_pool.calculate_tokens_in(token_out, "1.0")
    assert isinstance(amount_in, str)

    # Test invalid token
    with pytest.raises(ValueError):
        test_pool.calculate_tokens_in("INVALID", "1.0")

    # Test insufficient liquidity
    with pytest.raises(ValueError):
        test_pool.calculate_tokens_in(token_out, "9999999999999999")


def test_get_tokens(test_pool):
    tokens = test_pool.get_tokens()
    assert isinstance(tokens, list)
    assert len(tokens) == 2
    assert all(isinstance(token, str) for token in tokens)
