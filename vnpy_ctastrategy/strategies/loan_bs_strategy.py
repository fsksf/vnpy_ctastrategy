"""
融资融券策略
"""
from typing import Any, Callable, Dict
from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
from vnpy_ctastrategy.template import CtaTemplate


class LoanBSStrategy(CtaTemplate):

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        if self.pos == 0:
            self.preBookLoanSell(bar.close_price, volume=100)
        elif self.pos < 0:
            self.enBuyBack(volume=abs(self.pos), limit_price=bar.close_price)
        else:
            self.sell(limit_price=bar.close_price, volume=self.pos)
