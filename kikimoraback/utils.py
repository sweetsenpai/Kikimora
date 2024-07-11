from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

client = MongoClient(os.environ.get("MONGOCON"))
db = client['kikimora']
cart = db['cart']
print(db.list_collection_names())