# -*- coding:utf-8 -*-
"""
@FileName  :etf_template.py
@Time      :2022/10/26 13:48
@Author    :fsksf

对策略模板进行改造，使其支持多标的买卖、持仓，篮子，申赎
"""
from abc import ABC
from copy import copy
from typing import Any, Callable, Dict
import collections
from vnpy_ctastrategy.template import CtaTemplate
from vnpy.trader.constant import Interval, Direction, Offset, OrderType, Exchange
from vnpy.trader.object import (
    BarData, TickData, OrderData, TradeData, SubscribeRequest, OrderRequest,
    ContractData
)


class ETFTemplate(CtaTemplate):

    author = 'kyq'
    per_order_vol = 900000
    pre_ss_vol = 900000
    parameters = ['pre_ss_vol', 'per_order_vol']         # 申赎最小单位
    trade_basket = True

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,         # 篮子对应的ETF
        setting: dict,
        trade_basket: bool = True  # 是否交易篮子，关系到是否订阅ETF对应的篮子
    ):
        """"""
        super(ETFTemplate, self).__init__(cta_engine,
                                          strategy_name,
                                          vt_symbol,  # 篮子对应的ETF
                                          setting)
        self.cta_engine = cta_engine
        self.strategy_name = strategy_name
        self.vt_symbol = vt_symbol
        self.trade_basket = trade_basket

        self.inited = False
        self.trading = False
        self.pos = collections.defaultdict(lambda: 0)
        self.target_basket_pos = 0          # 篮子目标数量
        self.require_basket_pos = {}        # 篮子成分股每个股票还需要买多少
        self.basket_pos = 0                 # 篮子包数量（成分股折算）
        self.etf_pos = 0                    # etf的数量(折算)
        self.all_pos = 0                    # 总量 etf + basket_vol （折算）
        self.per_order_vol = 100000             # 每次下单最多多少，分批下单，减少冲击
        self.pre_ss_vol = 900000                # 申赎最小单位

        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "etf_pos")
        self.variables.insert(3, "basket_pos")
        self.variables.insert(4, "pos")
        self.variables.insert(6, "all_pos")

        self.update_setting(setting)

    def get_etf_stocks_sub_reqs(self):
        if self.trade_basket:
            return [SubscribeRequest(symbol=comp.symbol,
                                     exchange=comp.exchange,
                                     important=False)
                    for comp in self.cta_engine.main_engine.get_basket_components(self.vt_symbol)]
        else:
            return []

    def on_trade(self, trade: TradeData):
        self.etf_pos = self.pos[self.vt_symbol]
        self.calc_basket_pos()

    def on_start(self):
        self.calc_basket_pos()

    def calc_basket_pos(self):
        """计算持仓"""
        self.require_basket_pos = {}
        contract = self.cta_engine.main_engine.get_contract(self.vt_symbol)
        target_basket_pos = self.target_basket_pos
        basket_pos = float('inf')
        for comp in self.cta_engine.main_engine.get_basket_components(self.vt_symbol):
            # 只买卖同市场
            if comp.exchange != contract.exchange:
                continue
            share = comp.share
            if share == 0:
                continue

            # 处理涨跌停
            cash_flag = comp.cash_flag()
            if cash_flag == 2:
                continue
            elif cash_flag == 1:
                tick = self.cta_engine.main_engine.get_tick(comp.vt_symbol)
                if tick is None:
                    continue
                if tick and tick.last_price == tick.limit_up or tick.last_price == tick.limit_down:
                    print(f'{tick.vt_symbol} 涨停或者跌停，up: {tick.limit_up}, down {tick.limit_down} '
                          f'last price {tick.last_price}')
                    continue

            comp_current_pos = self.pos[comp.vt_symbol]
            # 篮子合成持仓，取小
            _basket_pos = comp_current_pos / share
            if _basket_pos < basket_pos:
                basket_pos = _basket_pos

            comp_target_pos = share * target_basket_pos
            comp_require_pos = comp_target_pos - comp_current_pos
            if comp_require_pos != 0:
                self.require_basket_pos[comp.vt_symbol] = comp_require_pos
        self.basket_pos = basket_pos
        self.etf_pos = self.pos[self.vt_symbol] / self.pre_ss_vol
        self.all_pos = self.etf_pos + self.basket_pos

    def buy_sell_with_target(
        self,
        limit_price: float,
        target_volume: float,
        per_order_max: float,
        signal_price: float = None,
        stop: bool = False,
        lock: bool = False,
        net: bool = False
    ):
        """
        根据目标仓位和每批次下单量etf下单
        :param target_volume: 目标仓位
        :param per_order_max: 分批下单本次最多的数量
        :return:
        """
        vol_gap = target_volume - self.all_pos * self.pre_ss_vol         # 仓位缺口
        this_vol = min(abs(vol_gap), per_order_max)
        if vol_gap > 0:
            return self.buy(
                limit_price=limit_price,
                volume=this_vol,
                signal_price=signal_price,
                stop=stop,
                lock=lock,
                net=net
            )
        elif vol_gap < 0:
            return self.sell(
                limit_price=limit_price,
                volume=this_vol,
                signal_price=signal_price,
                stop=stop,
                lock=lock,
                net=net
            )
        return ""

    def purchase(self, volume):
        """
        申购
        """
        return self.send_order(price=0, volume=volume, direction=Direction.PURCHASE, offset=Offset.NONE,
                               lock=False)

    def redemption(self, volume):
        """
        赎回
        """
        return self.send_order(price=0, volume=volume, direction=Direction.REDEMPTION, offset=Offset.NONE,
                               lock=False)

    def set_basket_target(self, target_volume):
        """
        买卖篮子设置篮子目标仓位，系统会根据目标仓位进行计算买卖逻辑. 如果是卖出，应该设置target_volume=0
        :param target_volume:
        :return:
        """
        self.target_basket_pos = target_volume
        self.calc_basket_pos()
        order_requests = []
        for k, v in self.require_basket_pos.items():
            contract: ContractData = self.cta_engine.main_engine.get_contract(k)
            if not contract:
                continue
            if v > 0:
                order_requests.append(OrderRequest(
                    direction=Direction.LONG,
                    offset=Offset.OPEN,
                    price=0,
                    volume=v,
                    signal_price=None,
                    symbol=contract.symbol,
                    exchange=contract.exchange,
                    gateway_name=contract.gateway_name,
                    type=OrderType.BestOrLimit)
                )
            elif v < 0:
                order_requests.append(OrderRequest(
                    direction=Direction.SHORT,
                    offset=Offset.CLOSE,
                    price=0,
                    volume=abs(v),
                    signal_price=None,
                    symbol=contract.symbol,
                    exchange=contract.exchange,
                    gateway_name=contract.gateway_name,
                    type=OrderType.BestOrLimit)
                )
        order_ids = self.cta_engine.send_order_many(self, order_requests)
        self.active_orderids.update(order_ids)
        return order_ids

    def get_data(self):
        """
        Get strategy data.
        """
        data = super().get_data()
        data['trade_basket'] = self.trade_basket
        return data
