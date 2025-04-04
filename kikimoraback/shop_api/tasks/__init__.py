from .db_tasks.cache_tasks.cache_on_start_tasks import boot_cache
from .db_tasks.cache_tasks.cache_prices_tasks import cache_result, update_price_cache

from .db_tasks.mongo.mongo_tasks import clean_up_mongo

from .db_tasks.sql.discounts_tasks import activate_discount, deactivate_expired_discount
from .db_tasks.sql.filling_db_tasks import check_crm_changes
from .db_tasks.sql.limit_time_tasks import delete_limite_time_product
from .db_tasks.sql.promo_tasks import activate_promo, deactivate_expired_promo

from .emails.user_emails import send_confirmation_email
from .emails.admin_emails import new_admin_mail, feedback_email
from .emails.order_emails import new_order_email

from .payment_tasks.payment_canceled_tasks import process_payment_canceled
from .payment_tasks.payment_succeeded_tasks import process_payment_succeeded

__all__ = [
    "boot_cache",
    "cache_result", "update_price_cache",

    "clean_up_mongo",

    "activate_discount", "deactivate_expired_discount",
    "check_crm_changes",
    "delete_limite_time_product",
    "activate_promo", "deactivate_expired_promo",

    "send_confirmation_email",
    "new_admin_mail",
    "feedback_email",
    "new_order_email",

    "process_payment_canceled",
    "process_payment_succeeded",
]

