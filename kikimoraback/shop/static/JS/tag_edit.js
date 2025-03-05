$(document).ready(function () {
    let tagId = $("#tagId").val();  // Получаем ID тега
    if (!tagId) {
        console.error("Ошибка: не найден ID тега.");
        return;
    }

    // Автозаполнение текстового поля тегом
    $("#tagName").val("{{ tag.text }}");

    // Получаем список товаров
    let productList = $("#productList");
    let products = JSON.parse('{{ products|safe }}');  // Конвертируем данные в JS-объект
    productList.empty();
    products.forEach(product => {
        productList.append(`<li data-id="${product.product_id}">${product.name}</li>`);
    });

    // Обработчик кнопки удаления тега
    $("#deleteTag").click(function () {
        $.ajax({
            url: `/admin/tags/delete/${tagId}/`,
            type: "POST",
            headers: { "X-CSRFToken": "{{ csrf_token }}" },
            success: function (response) {
                alert("Тег удалён!");
                window.location.href = "/admin/tags/";  // Редирект после удаления
            },
            error: function () {
                alert("Ошибка при удалении тега.");
            }
        });
    });
});
