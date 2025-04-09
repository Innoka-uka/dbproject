import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid

import pytest
import uuid


class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家和卖家信息
        self.seller_id = "test_cancel_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_cancel_order_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_cancel_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        self.gen_book = GenBook(self.seller_id, self.store_id)
        
        # 创建一个有效的订单用于测试
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        yield

    def test_ok(self):
        # 测试正常取消订单
        code = self.buyer.cancel_order( self.order_id)
        assert code == 200

    def test_invalid_order_id(self):
        # 测试无效的订单 ID
        invalid_order_id = str(uuid.uuid1())
        code = self.buyer.cancel_order(invalid_order_id)
        assert code != 200


    def test_already_cancelled(self):
        # 测试重复取消订单
        code = self.buyer.cancel_order( self.order_id)
        assert code == 200

        # 再次尝试取消同一个订单
        code = self.buyer.cancel_order( self.order_id)
        assert code != 200


