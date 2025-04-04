from celery import shared_task
import pymongo
import logging
logger = logging.getLogger(__name__)


@shared_task
def clean_up_mongo():
    collection = pymongo.MongoClient(os.getenv("MONGOCON"))['kikimora']['cart']
    result = collection.delete_many({"unregistered": True})
    logger.info(f"Удалено {result.deleted_count} корзин с меткой unregistered.")