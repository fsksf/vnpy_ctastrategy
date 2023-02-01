# -*- coding: utf-8 -*-
"""
@Time    : 2023/1/31 14:56
@Author  : fsksf
@File    : cta_spread_strategy1.py
"""
import time
from vnpy_ctastrategy.spread_template import CtaSpreadTemplate


class CtaSpreadStrategy1(CtaSpreadTemplate):

    last_order_time = 0

    def handle_tick(self, leg_a_lack, leg_b_lack):
        tick_a = self.ticks.get(self.leg_a)
        tick_b = self.ticks.get(self.leg_b)
        if not (tick_a and tick_b):
            return
        # 超过60s还有订单未完成，取消所有订单
        if not self.all_order_finished():
            if time.time() - self.last_order_time > 60:
                self.cancel_all()
            return
        if leg_a_lack > 0 and tick_a:
            new_order = True
            self.buy(vt_symbol=self.leg_a, limit_price=tick_a.last_price,
                     volume=leg_a_lack * self.leg_a_mult, lock=True)
        if leg_b_lack > 0 and tick_b:
            new_order = True
            self.buy(vt_symbol=self.leg_b, limit_price=tick_b.last_price,
                     volume=leg_b_lack * self.leg_b_mult, lock=True)
        if leg_a_lack < 0 and tick_a:
            new_order = True
            self.sell(vt_symbol=self.leg_a, limit_price=tick_a.last_price,
                      volume=abs(leg_a_lack) * self.leg_a_mult, lock=True)
        if leg_b_lack < 0 and tick_b:
            new_order = True
            self.sell(vt_symbol=self.leg_b, limit_price=tick_b.last_price,
                      volume=abs(leg_b_lack) * self.leg_b_mult, lock=True)
        if new_order:
            self.last_order_time = time.time()