import pytest
import uuid
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller

class TestShipOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化卖家和商店信息
        self.seller_id = "test_ship_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_ship_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_ship_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id

        # 注册卖家和买家
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # 初始化书籍生成器
        self.gen_book = GenBook(self.seller_id, self.store_id)

        # 创建一个有效的订单并插入到数据库中
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200


        yield

    def test_ok(self):
        self.buyer.payment(self.order_id)
        # 测试正常发货订单
        code = self.seller.ship_order( self.store_id, self.order_id)
        assert code == 200

    def test_non_exist_store_id(self):
        # 测试商店 ID 不存在的情况
        non_existent_store_id = str(uuid.uuid1())
        code= self.seller.ship_order( non_existent_store_id, self.order_id)
        assert code != 200

    def test_invalid_order_id(self):
        # 测试无效的订单 ID
        invalid_order_id = str(uuid.uuid1())
        code,= self.seller.ship_order(self.store_id, invalid_order_id)
        assert code != 200

    def test_order_not_paid(self):
        code = self.seller.ship_order( self.store_id, self.order_id)
        assert code != 200

    def test_repeat(self):
        self.buyer.payment(self.order_id)
        code = self.seller.ship_order( self.store_id, self.order_id)
        assert code == 200
        code = self.seller.ship_order( self.store_id, self.order_id)
        assert code != 200