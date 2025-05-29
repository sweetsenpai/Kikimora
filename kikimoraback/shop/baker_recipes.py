from itertools import product

from django.utils import timezone

from model_bakery.recipe import Recipe, foreign_key, related

from shop.models import Category, Discount, Product, Subcategory, PromoSystem

category_recipe = Recipe(
    Category,
)

subcategory_recipe = Recipe(Subcategory, category=foreign_key(category_recipe))

product_recipe = Recipe(Product)

product_recipe_with_subs = product_recipe.extend(subcategory=related(subcategory_recipe))


discount_category_recipe = Recipe(
    Discount,
    discount_type="percentage",
    value=50,
    start=timezone.now(),
    end=timezone.now() + timezone.timedelta(days=30),
    category=foreign_key(category_recipe),
    active=True,
)

discount_subcategory_recipe = Recipe(
    Discount,
    discount_type="amount",
    value=50,
    start=timezone.now(),
    end=timezone.now() + timezone.timedelta(days=30),
    subcategory=foreign_key(subcategory_recipe),
    active=True,
)

discount_product_recipe = Recipe(
    Discount,
    discount_type="amount",
    value=50,
    start=timezone.now(),
    end=timezone.now() + timezone.timedelta(days=30),
    product=foreign_key(product_recipe_with_subs),
    active=True,
)


promocode_recipe = Recipe(
    PromoSystem,
    promo_product=foreign_key(product_recipe_with_subs),
    type='delivery',
    start=timezone.now(),
    end=timezone.now() + timezone.timedelta(days=30),
)
