host = '127.0.0.1'
port = 27017
database = 'LiePin'

import time

start = time.clock()

from pymongo import MongoClient

connection = MongoClient(
    host,
    port
)
db = connection[database]

for doc in db.LiePin_Analysis1.find({}, ['_id', 'JobTitle', 'is_end']):
    db.LiePin_Analysis1.update_one({'_id': doc.get('_id')}, {
        '$set': {
            'is_end': 1
        }
    })

elapsed = (time.clock() - start)
print("Time used:", elapsed)