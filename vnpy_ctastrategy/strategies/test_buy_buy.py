# -*- coding:utf-8 -*-
"""
@FileName  :etf_cta_strategy.py
@Time      :2022/10/27 10:44
@Author    :fsksf
"""
from typing import Any, Callable, Dict
from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
# 注意这里引入的是ETFTemplate
from vnpy_ctastrategy.etf_template import ETFTemplate


class ETFBuyBuy(ETFTemplate):
    etf_shenshu_min_vol = 2000000
    parameters = ['etf_shenshu_min_vol']

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,         # 篮子对应的ETF
        setting: dict,
        trade_basket: bool = True
    ):
        super(ETFBuyBuy, self).__init__(cta_engine, strategy_name, vt_symbol, setting,
                                        trade_basket=trade_basket)

        self.bg = BarGenerator(on_bar=self.on_bar)

    def on_tick(self, tick: TickData):
        """
        这里之做bar的合成
        :param tick:
        :return:
        """
        self.bg.update_tick(tick)
        self.handle_tick(tick)

    def handle_tick(self, tick):
        """
        tick级别的策略逻辑写在这里
        :param tick:
        :return:
        """
        pass

    def on_bar(self, bar: BarData):
        """
        这里只做历史数据队列的存储
        :param bar:
        :return:
        """
        self.handle_bar(bar)

    def handle_bar(self, bar: BarData):
        """
        bar级别的策略逻辑可以写在这里
        :param bar:
        :return:
        """
        self.cancel_all()
        self.buy(limit_price=bar.close_price, volume=100)
