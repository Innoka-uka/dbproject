import json
import pytest
import uuid

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access import auth
from fe.access import book
from fe import conf


class TestSearchBook:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化卖家和商店信息
        self.seller_id = "test_search_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_search_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        self.auth = auth.Auth(conf.URL)

        # 注册买家
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # 初始化书籍生成器
        self.gen_book = GenBook(self.seller_id, self.store_id)
        self.seller = self.gen_book.seller
        book_db = book.BookDB()
        self.book_example = book_db.get_book_info(0, 1)[0]


    def test_search_by_title(self):
        # 测试通过标题搜索
        title = "美丽心灵"
        code = self.auth.search_book(title=title)
        assert code == 200


    def test_search_by_content(self):
        # 测试通过内容搜索
        content = ""
        code = self.auth.search_book(content=content)
        assert code == 200


    def test_search_by_tag(self):
        # 测试通过标签搜索
        tag = "传记"
        code = self.auth.search_book(tag=tag)
        assert code == 200


    def test_search_by_store_id(self):
        # 测试通过商店 ID 搜索
        self.seller.add_book(self.store_id, 0, self.book_example)
        code = self.auth.search_book(store_id=self.store_id)
        assert code == 200

    def test_search_with_empty_query(self):
        code= self.auth.search_book()
        assert code == 200

    def test_search_with_non_existent_store_id(self):
        non_existent_store_id = str(uuid.uuid1())
        code = self.auth.search_book(store_id=non_existent_store_id)
        assert code != 200

    def test_no_books_found(self):
        # 测试没有找到书籍的情况
        invalid_title = "Non Existent Title"
        code= self.auth.search_book(title=invalid_title)
        assert code != 200

