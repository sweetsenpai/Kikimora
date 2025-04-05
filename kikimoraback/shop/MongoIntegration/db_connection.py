import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class MongoDBClient:
    _instance = None

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            mongo_uri = os.getenv("MONGOCON")
            cls._instance = MongoClient(mongo_uri)
        return cls._instance

    @classmethod
    def close_connection(cls):
        if cls._instance:
            cls._instance.close()
            cls._instance = None
