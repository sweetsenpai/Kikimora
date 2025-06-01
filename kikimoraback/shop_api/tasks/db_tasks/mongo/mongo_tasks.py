import logging
import os

import pymongo
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def clean_up_mongo():
    collection = pymongo.MongoClient(os.getenv("MONGOCON"))["kikimora"]["cart"]
    result = collection.delete_many({"unregistered": True})
    logger.info(f"Удалено {result.deleted_count} корзин с меткой unregistered.")
