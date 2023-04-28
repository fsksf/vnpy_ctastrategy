# -*- coding:utf-8 -*-
"""
@FileName  :etf_cta_strategy_shengou.py
@Time      :2022/10/27 10:44
@Author    :fsksf

ETF 赎回示例
"""
from typing import Any, Callable, Dict
from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
# 注意这里引入的是ETFTemplate
from vnpy_ctastrategy.etf_template import ETFTemplate


class ETFBSStrategyShuHui(ETFTemplate):

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,         # 篮子对应的ETF
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.am = ArrayManager(size=100)
        self.bg = BarGenerator(on_bar=self.on_bar)
        self.tick: TickData = None

    def on_init(self):
        self.load_bar(1)

    def on_tick(self, tick: TickData):
        """
        这里之做bar的合成
        :param tick:
        :return:
        """
        self.tick = tick
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
        # self.am.update_bar(bar)
        # if not self.am.inited:
        #     return
        # if not self.trading:
        #     return
        self.handle_bar(bar)

    def handle_bar(self, bar: BarData):
        """
        bar级别的策略逻辑可以写在这里
        :param bar:
        :return:
        """
        self.cancel_all()
        # spread = self.get_spread("IM159845-1")
        etf_symbol = self.vt_symbol
        dDiscount, dPremium = self.get_moment_profit(etf_symbol)
        # print(f'cta策略中取到了 价差：{spread.name} 价格为：{spread.last_price}')
        print(f'cta策略中取到了 {etf_symbol} 的瞬时利润： discount: {dDiscount}, premium: {dPremium}')

        if self.basket_pos < 1 and self.etf_pos == 0:
            print('买入ETF')
            self.buy_sell_with_target(limit_price=self.tick.ask_price_1,
                                      target_volume=self.pre_ss_vol,
                                      per_order_max=self.pre_ss_vol,
                                      )

        elif self.etf_pos >= self.pre_ss_vol:
            print('赎回')
            self.redemption(1)
        elif self.basket_pos >= 1:
            print('卖出篮子')
            self.set_basket_target(target_volume=0)
