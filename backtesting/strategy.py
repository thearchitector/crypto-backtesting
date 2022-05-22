from abc import ABC
from typing import Dict, List, Tuple, final

import pandas

Wallet = List[float]


class Strategy(ABC):
    """
    Base class used to create different trading strategies. Custom preprocessing or
    initialization should happen in `__init__` after calling `super()`.
    """

    def __init__(self, rates: Dict[str, pandas.DataFrame], coins: Dict[str, int]):
        self.rates = rates
        self.coins = coins

    def calculate_fee(self, coin: str, timestep: int, amount: float) -> Tuple[int, str]:
        """
        Calculates the trading fees on the given amount of the given coin at a specific
        time. Returns both the fee, and the coin to deduct from (fee-coin). By default,
        trading fees deduct from the coin in trade, and are 0.
        """
        return 0, coin

    def trade(self, coin: str, timestep: int, wallet: Wallet, *args):
        raise NotImplementedError("Strategies must implement a trading algorithm!")

    @final
    def buy(self, timestep: int, coin: str, amount: float, wallet: Wallet):
        """
        Simulates a "buy" call at the given timestep for a given amount of coin. A buy
        will only occur if the wallet has enough USDC and fee-coin.
        """
        # calculate a transaction fee
        fee, fee_coin = self.calculate_fee(coin, timestep, amount)
        fcoin = self.coins[fee_coin]
        # ensure the wallet has enough of USDC and fee-coin
        if fcoin == 0:
            can_trade = wallet[0] >= (amount + fee)
        else:
            can_trade = wallet[0] >= amount and wallet[fcoin] >= fee

        # if the user has enough to trade
        if can_trade:
            wallet[fcoin] -= fee
            wallet[0] -= amount  # wallet 0 is always USDC
            wallet[self.coins[coin]] += amount / self.rates[coin][timestep - 1]

    @final
    def sell(self, timestep: int, coin: str, amount: float, wallet: Wallet):
        """
        Simulates a "see" call at the given timestep for a given amount of coin. A sell
        will only occur if the wallet has enough of coin and fee-coin.
        """
        fee, fee_coin = self.calculate_fee(coin, timestep, amount)
        fcoin = self.coins[fee_coin]
        coini = self.coins[coin]
        if fee_coin == coin:
            can_trade = wallet[coini] >= (amount + fee)
        else:
            can_trade = wallet[coini] >= amount and wallet[fcoin] >= fee

        if can_trade:
            wallet[fcoin] -= fee
            wallet[coini] -= amount
            wallet[0] += amount * self.rates[coin][timestep - 1]
