import pytest
import uuid
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer

class TestReceiveOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家和卖家信息
        self.seller_id = "test_receive_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_receive_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_receive_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        # 注册买家
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # 初始化书籍生成器
        self.gen_book = GenBook(self.seller_id, self.store_id)
        self.seller = self.gen_book.seller

        # 创建一个有效的订单并插入到数据库中
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        yield

    def test_ok(self):
        code = self.seller.ship_order(self.store_id, self.order_id)
        # 测试正常接收订单
        code = self.buyer.receive_order( self.order_id)
        assert code == 200


    def test_invalid_order_id(self):
        # 测试无效的订单 ID
        invalid_order_id = str(uuid.uuid1())
        code = self.buyer.receive_order(invalid_order_id)
        assert code != 200

    def test_books_repeat_receive(self):
        code = self.seller.ship_order(self.store_id, self.order_id)
        assert code == 200
        code = self.buyer.receive_order( self.order_id)
        assert code == 200
        code = self.buyer.receive_order( self.order_id)
        assert code != 200
 