from typing import Dict, List, Type, final

import pandas

from .strategy import Strategy, Wallet


class Simulation:
    """
    Sets up and runs a simulation of trading activity using the given strategy over the
    loaded data, with the ability to tune or optimize arbitrary strategy
    hyperparamaters.
    """

    def __init__(
        self,
        duration: int,
        strategy_class: Type[Strategy],
        rates: Dict[str, pandas.DataFrame],
        coins: Dict[str, int],
        starting_value: int,
    ):
        if not rates.keys() == coins.keys():
            raise ValueError(
                "Data mismatch! The strategy must have rates corresponding to each coin"
                " to trade, and each coin must have an initial value."
            )

        self.duration = duration
        """
        The duration of time the simulation should run for, counting from the end of
        the timeseries. The base unit of time depends on the resolution of the loaded
        data.

        For example, if this is set to `365` and the loaded data is day by day, the
        simulation will run for the last 365 days. If the loaded data is hour by hour,
        however, the simulation will only run for the last 365 hours.
        """
        initials = []
        cmap = {"USDC": 0}
        for i, (coin, init) in enumerate(coins.items()):
            cmap[coin] = i + 1
            initials.append(init)

        for k in rates.keys():
            rates[k] = rates[k][-duration:]
        self.strategy = strategy_class(
            rates=rates,
            coins=cmap,
        )
        self.coins = coins.keys()
        """
        The coins with which to trade. This excludes USDC, which is the default
        collateral to use."""
        self.wallets: List[Wallet] = [[starting_value, *initials, starting_value]]

    @final
    def simulate(self, *args) -> List[Wallet]:
        # for every timestep in simulation duration
        for timestep in range(1, self.duration + 1):
            wallet = self.wallets[timestep - 1].copy()

            for coin in self.coins:
                self.strategy.trade(coin, timestep, wallet, *args)

            # calculate the current wallet value
            wallet[3] = wallet[0] + sum(
                wallet[i + 1] * self.strategy.rates[coin][timestep - 1]
                for i, coin in enumerate(self.coins)
            )

            self.wallets.append(wallet)

        return self.wallets
