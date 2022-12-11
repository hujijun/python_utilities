from sanic_mongo import GridFS

MONGO_URI = "mongodb://localhost:27017/dev"


GridFS.SetConfig(app, test_fs=(MONGO_URI,"fs"))
GridFS(app)
