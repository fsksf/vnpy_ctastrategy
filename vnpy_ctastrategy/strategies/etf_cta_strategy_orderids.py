# -*- coding:utf-8 -*-
"""
@FileName  :etf_cta_strategy_shengou.py
@Time      :2022/10/27 10:44
@Author    :fsksf
"""
import random
import time
from typing import Any, Callable, Dict
from vnpy.trader.utility import ArrayManager, BarGenerator
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
# 注意这里引入的是ETFTemplate
from vnpy_ctastrategy.etf_template import ETFTemplate


class ETFBSStrategyOrderIds(ETFTemplate):

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,         # 篮子对应的ETF
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(on_bar=self.on_bar)
        self.active_order_ids = set()
        self.pre_order_time = time.time()


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
        if self.active_order_ids and time.time() - self.pre_order_time < 10:
            print('还有30s内的订单未完全成交')
            return
        if self.active_order_ids:
            print('挂单超过30s，撤单')
            self.cancel_all()
        print('下单')
        vol = random.choice([100, 500, 40000, 50000, 100, 500, 200, 300, 400, 600, 700, 800])
        self.active_order_ids.update(self.buy(limit_price=2.6, volume=vol))

    def on_order(self, order: OrderData):
        if not order.is_active():
            if order.vt_orderid not in self.active_order_ids:
                return
            self.active_order_ids.remove(order.vt_orderid)

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
        print(self.get_pos_factor())
