import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import pymongo

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.decode("utf-8")


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False
        
    # 前40 -注册
    def register(self, user_id: str, password: str):
        try:
            # Check if user with the same user_id already exists
            existing_user = self.conn['user'].find_one({"user_id": user_id})
            if existing_user:
                return error.error_exist_user_id(user_id)

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            user_data = {
                "user_id": user_id,
                "password": password,
                "balance": 0,
                "token": token,
                "terminal": terminal
            }
            self.conn['user'].insert_one(user_data)
            return 200, "ok"
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)

    # 前40 -登录1
    def check_token(self, user_id: str, token: str) -> (int, str):
        users = self.conn['user'].find_one({'user_id': user_id})
        if users is None:
            return error.error_authorization_fail()

        db_token = users.get('token', '')
        is_token_valid = self.__check_token(user_id, db_token, token)
        if not is_token_valid:
            return error.error_authorization_fail()

        return 200, "ok"

    # 前40 - 登录2
    def check_password(self, user_id: str, password: str) -> (int, str):
        try:
            # 查询用户是否存在
            user = self.user_collection.find_one({"user_id": user_id}, {"password": 1})
            if user is None:
                return error.error_authorization_fail()

            # 检查密码是否匹配
            if password != user.get("password"):
                return error.error_authorization_fail()

        except pymongo.errors.PyMongoError as e:
            return 528, str(e)

        return 200, "ok"

    # 前40 - 登录
    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            result = self.conn['user'].update_one(
                {'user_id': user_id},
                {'$set': {'token': token, 'terminal': terminal}}
            )
            if not result.matched_count:
                return error.error_authorization_fail()
        except pymongo.errors.PyMongoError as e:
            return 528, str(e), ""
        except Exception as e:
            return 530, str(e), ""
        return 200, "ok", token

    # 前40 - 登出
    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            result = self.conn['user'].update_one(
                {'user_id': user_id},
                {'$set': {'token': dummy_token, 'terminal': terminal}}
            )
            if not result.matched_count:
                return error.error_authorization_fail()
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)
        except Exception as e:
            return 530, str(e)
        return 200, "ok"

    # 前40 - 注销
    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            result = self.conn['user'].delete_one({'user_id': user_id})
            if result.deleted_count != 1:
                return error.error_authorization_fail()
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)
        except Exception as e:
            return 530, str(e)
        return 200, "ok"

    # 前40 - 修改密码
    def change_password(self, user_id: str, old_password: str, new_password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            self.conn['user'].update_one(
                {'user_id': user_id},
                {'$set': {
                    'password': new_password,
                    'token': token,
                    'terminal': terminal,
                }},
            )
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)
        except Exception as e:
            return 530, str(e)
        return 200, "ok"

    # 后40-搜索图书
    def search_book(self, title='', content='', tag='', store_id=''):
        try:
            query = {}

            if title:
                query['title'] = {"$regex": title}
            if content:
                query['content'] = {"$regex": content}
            if tag:
                query['tags'] = {"$regex": tag}

            if store_id:
                store_query = {"store_id": store_id}
                store_result = self.conn["store"].find_one(store_query, {"book_id": 1})
                if not store_result:
                    return error.error_non_exist_store_id(store_id)
                book_ids = [item["book_id"] for item in store_result.get("book_id", [])]
                query['id'] = {"$in": book_ids}

            results = list(self.conn["books"].find(query))
            if not results:
                return error.error_no_books_found
            else:
                return 200, "ok"
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)
        except Exception as e:
            return 530, "{}".format(str(e))

    # 创新- 收藏书籍
    def collect_book(self, user_id, book_id):
        try:
            # Check if the user exists in the collection
            existing_user = self.conn['user'].find_one({"_id": user_id})
            if not existing_user:
                return error.error_non_exist_user_id(user_id)

            # Check if the book and store combination is already in the user's collection
            if (book_id) in existing_user.get("collection", []):
                return error.error_exist_collection(book_id)

            # Update the user's collection with the new book and store
            self.conn['user'].update_one(
                {"_id": user_id},
                {"$addToSet": {"collection": (book_id)}}
            )
            return 200, "ok"
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)

    # 创新- 取消收藏书籍
    def uncollect_book(self, user_id, book_id, store_id):
        try:
            # Check if the user exists in the collection
            existing_user = self.conn['user'].find_one({"_id": user_id})
            if not existing_user:
                return error.error_non_exist_user_id(user_id)

            # Remove the specified book and store from the user's collection
            self.conn['user'].update_one(
                {"_id": user_id},
                {"$pull": {"collection": (book_id, store_id)}}
            )
            return 200, "ok"
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)
        
        
    # 创新- 获得收藏单
    def get_collection(self, user_id):
        try:
            # Check if the user exists in the collection
            existing_user = self.conn['user'].find_one({"_id": user_id})
            if not existing_user:
                return error.error_non_exist_user_id(user_id)

            # Return the user's collection
            collection = existing_user.get("collection", [])
            return 200, collection
        except pymongo.errors.PyMongoError as e:
            return 528, str(e)

