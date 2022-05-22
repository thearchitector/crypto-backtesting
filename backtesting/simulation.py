from typing import Dict, List, Type, final, Optional

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
        strategy_class: Type[Strategy],
        rates: Dict[str, pandas.DataFrame],
        coins: Dict[str, int],
        starting_value: int,
        start_datetime: str,
        end_datetime: Optional[str] = None
    ):
        if not rates.keys() == coins.keys():
            raise ValueError(
                "Data mismatch! The strategy must have rates corresponding to each coin"
                " to trade, and each coin must have an initial value."
            )
        elif not all(start_datetime in r.index for r in rates.values()):
            raise ValueError(
                "Data mismatch! The provided start datetime does not have associated"
                " for one or more of the provided coin trading rates. All coins must"
                " have data for the given start datetime and end datetime."
            )
        elif not end_datetime and len({r.index[-1] for r in rates.values()}) != 1:
            raise ValueError(
                "Data mismatch! The provided rates do not share a common end datetime."
                " You must be expicitly pass a common end datetime."
            )

        self.start_datetime = start_datetime
        """
        The datetime stamp on which to start the simulation. Should be a string of the
        same form as the `rates` timeseries. Most commonly, this is
        `YYYY-MM-DD hh:mm:ss`. Denomination data must exist for this date for all coins
        in the provided `rates` table.
        """
        self.end_datetime = end_datetime or next(iter(rates.values())).index[-1]
        """
        Optional. The datetime stamp on which to end the simulation. Should be a string
        of the same form as the `rates` timeseries. Most commonly, this is
        `YYYY-MM-DD hh:mm:ss`. Denomination data must exist for this date for all coins
        in the provided `rates` table. If no value is provided, the simulation will run
        until the end of the available data.
        """
        initials = []
        cmap = {"USDC": 0}
        for i, (coin, init) in enumerate(coins.items()):
            cmap[coin] = i + 1
            initials.append(init)

        for k in rates.keys():
            rates[k] = rates[k][self.start_datetime:self.end_datetime]  # type: ignore
        self.duration = len(next(iter(rates.values())))
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
