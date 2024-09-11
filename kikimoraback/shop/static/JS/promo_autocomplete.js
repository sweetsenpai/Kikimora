$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", "{{ csrf_token }}");
        }
    }
});

$(function() {
    $("#product").autocomplete({
        source: function(request, response) {
            $.ajax({
                url: "/api/autocomplete/product/",
                dataType: "json",
                data: {
                    term: request.term
                },
                success: function(data) {
                    // Обрабатываем данные и передаём в автокомплит
                    response($.map(data, function(item) {
                        return {
                            label: item.name,
                            value: item.name,
                            id: item.id  // Если вам нужно сохранить ID продукта
                        };
                    }));
                }
            });
        },
        minLength: 2,  // Начать показывать подсказки после ввода 2 символов
        select: function(event, ui) {
            $("#product").val(ui.item.value);  // Вставляем название продукта
            $("#product_id").val(ui.item.id);  // Вставляем ID продукта в скрытое поле
            return false;
        }

    });
});
