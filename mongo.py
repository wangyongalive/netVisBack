# coding=utf-8
import pymongo
import json

# 配置文件  字典
config = {
    'host': 'localhost',
    'port': 27017,
    'db': 'nodeLink',
    'collection': 'nodeLink'
}
client = pymongo.MongoClient(host=config['host'], port=config['port'])  # host为地址，port为端口（port的默认参数为27017）
db = client[config['db']]  # db数据库
collection = db[config['collection']]



# 将json数据导入到数据库中
def importJson(result,filename):
    global db
    # with open(uploadFiles) as fi:
    #     result = json.load(fi)
    db[filename].insert_one(result)

# 获取所有的数据
def get_all_data():
    results = collection.find()  # 查询生成一个生成器
    result = {}
    for res in results:  # 遍历输出
        result = {'nodes': res['nodes'], 'links': res['links']}
    return result


# 获取数据库 和 集合 的列表
def get_info(client, db):
    db_database_list = client.database_names()
    db_col_list = db.collection_names()
    return {
        'database': db_database_list,
        'db_col_list': db_col_list
    }


# 插入集合
def insert_one(col, mydict):
    return col.insert_one(mydict)


# res = insert_one(collection,{ "name": "Google", "alexa": "1", "url": "https://www.google.com" })
# print res.inserted_id

# 插入多个文档
def insert_many(col, mylist):
    return col.insert_many(mylist)


# res = insert_many(collection, mylist=[
#     {"name": "Taobao", "alexa": "100", "url": "https://www.taobao.com"},
#     {"name": "QQ", "alexa": "101", "url": "https://www.qq.com"},
#     {"name": "Facebook", "alexa": "10", "url": "https://www.facebook.com"},
#     {"name": "知乎", "alexa": "103", "url": "https://www.zhihu.com"},
#     {"name": "Github", "alexa": "109", "url": "https://www.github.com"}
# ])
# print res.inserted_ids

# 插入指定 _id 的多个文档
# res = insert_many(collection, [
#     {"_id": 1, "name": "RUNOOB", "cn_name": "菜鸟教程"},
#     {"_id": 2, "name": "Google", "address": "Google 搜索"},
#     {"_id": 3, "name": "Facebook", "address": "脸书"},
#     {"_id": 4, "name": "Taobao", "address": "淘宝"},
#     {"_id": 5, "name": "Zhihu", "address": "知乎"}
# ])
# print res.inserted_ids

# 查询 find
def find_one(col):
    return col.find_one()


# 查询所有
def find(col):
    find_all = {}
    for index, item in enumerate(col.find()):
        find_all[index] = item
    return find_all


# 查询指定字段的数据
# 使用 find() 方法来查询指定字段的数据，将要返回的字段对应值设置为 1
def find_get(col, config):
    find_all = {}
    for index, item in enumerate(col.find({}, config)):
        find_all[index] = item
    return find_all


# 除了 _id 你不能在一个对象中同时指定 0 和 1，如果你设置了一个字段为 0，则其他都为 1，反之亦然。
# res = find_get(collection, {"_id": 0, "name": 1, "alexa": 1})
# print res

# 根据指定条件查询
def find_query(col, config):
    find_all = {}
    for index, item in enumerate(col.find(config)):
        find_all[index] = item
    return find_all


# res = find_query(collection, {"name": "RUNOOB"})
# print res

# 高级查询
# res = find_query(collection, {"name": {'$gt': 'H'}})
# print res

# 使用正则表达式查询
# res = find_query(collection, {"name": {"$regex": "^R"}})
# print res

# 返回指定条数记录
def find_limit(col):
    find_all = {}
    for index, item in enumerate(col.find().limit(3)):
        find_all[index] = item
    return find_all


# res = find_limit(collection)
# print res


# 更新数据
def update(col, query, newvalues):
    # 更新一个
    # col.update_one(query, newvalues)
    # 更新所有
    col.update_many(query, newvalues)


# update(collection, {"alexa": "10000"}, {"$set": {"alexa": "12345"}})
# for x in collection.find():
#     print x

# 排序
def sort(col):
    # return col.find().sort('alexa')
    return col.find().sort('alexa', -1)


# res = sort(collection)
# for x in res:
#     print x


# 删除数据
def delete_one(col, query):
    # col.delete_one(query)
    # col.delete_many(query)
    # 删除所有的数据
    col.delete_many({})


# delete_one(collection, {"name": "Taobao"})

def drop(col):
    col.drop()
# drop(collection)