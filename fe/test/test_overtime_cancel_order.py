import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid

import time
import threading


class TestNewOrderWithTimer:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家和卖家信息
        self.seller_id = "test_timer_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_timer_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_timer_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id

        # 注册买家
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # 初始化书籍生成器
        self.gen_book = GenBook(self.seller_id, self.store_id)

        yield

    def test_timer_cancel_order(self):
        # 创建一个有效的订单
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        # 模拟等待 60 秒（通过调整时间加速）
        time.sleep(61)  # 等待定时器触发

        # 验证订单是否被取消
        code = self.buyer.cancel_order(order_id)
        assert code != 200  # 订单已经被定时器取消，无法再次取消


    def test_manual_cancel_before_timer(self):
        # 创建一个有效的订单
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        # 提前手动取消订单
        code = self.buyer.cancel_order( order_id)
        assert code == 200

        # 等待定时器触发
        time.sleep(61)  # 确保定时器触发

        # 再次尝试取消订单，确保定时器没有重复取消
        code = self.buyer.cancel_order( order_id)
        assert code != 200  # 定时器不应该重复取消



