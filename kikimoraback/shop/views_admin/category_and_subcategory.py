from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from shop.forms import CategoryCreationForm
from shop.mixins import StaffCheckRequiredMixin, is_staff_or_superuser
from shop.models import Category, Subcategory


class AdminCategoryView(StaffCheckRequiredMixin, ListView):
    """
    Представление для отображения списка категорий товаров в административной панели.

    Наследуется от:
        - StaffCheckRequiredMixin: миксин, проверяющий доступ администратора.
        - ListView: встроенное представление Django для отображения списка объектов.

    Атрибуты:
        template_name (str): путь к шаблону отображения списка категорий.
        context_object_name (str): имя переменной, под которым категории будут доступны в шаблоне.
        form_class (CategoryCreationForm): форма для создания новой категории (не используется напрямую здесь, но может использоваться в шаблоне).
        queryset (QuerySet): список всех категорий, отсортированных по `category_id`.
    """

    template_name = "master/product/category.html"
    context_object_name = "categories"
    form_class = CategoryCreationForm
    queryset = Category.objects.all().order_by("category_id")


@user_passes_test(is_staff_or_superuser)
def toggle_visibility_category(request, category_id: int):
    """
    Обрабатывает запрос на переключение видимости категории товара в админке.

    Доступ разрешён только администраторам (is_staff или is_superuser).

    Метод:
        POST — инвертирует текущее значение поля `visibility` у категории с указанным ID.

    Аргументы:
        request (HttpRequest): объект запроса.
        category_id (int): идентификатор категории, видимость которой нужно изменить.

    Возвращает:
        JsonResponse:
            - {"visibility": bool} при успешной смене видимости (HTTP 200).
            - {"error": "Invalid request"} при некорректном методе запроса (HTTP 400).
    """
    if request.method == "POST":
        category = get_object_or_404(Category, pk=category_id)
        category.visibility = not category.visibility
        category.save()
        return JsonResponse({"visibility": category.visibility})
    return JsonResponse({"error": "Invalid request"}, status=400)


class AdminSubcategoryListView(StaffCheckRequiredMixin, ListView):
    """
    Представление для отображения списка подкатегорий,
    принадлежащих определённой категории, доступное только для сотрудников.

    Атрибуты:
        model (Model): Модель Subcategory.
        template_name (str): Путь к шаблону для отображения подкатегорий.
        context_object_name (str): Имя переменной в контексте шаблона.

    Методы:
        get_queryset(): Возвращает QuerySet подкатегорий, отфильтрованный по категории.
        get_context_data(**kwargs): Добавляет объект категории в контекст шаблона.
    """

    template_name = "master/product/subcategory.html"
    context_object_name = "subcategories"
    queryset = Subcategory.objects.all()
    # def get_queryset(self):
    #     self.category = get_object_or_404(Category, pk=self.kwargs["category_id"])
    #     return Subcategory.objects.filter(category=self.category).order_by("subcategory_id")
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context["category"] = self.category
    #     return context


@user_passes_test(is_staff_or_superuser)
def toggle_visibility_subcat(request, subcategory_id):
    """
    Обрабатывает запрос на переключение видимости подкатегории товара в админке.

    Доступ разрешён только администраторам (is_staff или is_superuser).

    Метод:
        POST — инвертирует текущее значение поля `visibility` у категории с указанным ID.

    Аргументы:
        request (HttpRequest): объект запроса.
        category_id (int): идентификатор категории, видимость которой нужно изменить.

    Возвращает:
        JsonResponse:
            - {"visibility": bool} при успешной смене видимости (HTTP 200).
            - {"error": "Invalid request"} при некорректном методе запроса (HTTP 400).
    """
    if request.method == "POST":
        subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
        subcategory.visibility = not subcategory.visibility
        subcategory.save()
        return JsonResponse({"visibility": subcategory.visibility})
    return JsonResponse({"error": "Invalid request"}, status=400)
