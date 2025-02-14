$(document).on('click', '#submit-button', function(event) {
    event.preventDefault(); // Предотвратить отправку формы
    console.log("Кнопка нажата");

    // Сохраним ссылку на элемент формы
    var formElement = $(this).closest("form");

    // Создаем диалоговое окно
    $.confirm({
        title: 'Удаление сотрудника',
        content: 'Вы уверены, что хотите удалить этого сотрудника?\nСомневаюсь, что после удаления мы сможем всё исправить если Вы передумаете!',
        type: 'red',
        buttons: {
            Создать: {
                text: 'Удалить',
                btnClass: 'btn-red',
                action: function() {
                    console.log("Попробовать снова нажать");

                    // Ваш AJAX-запрос здесь
                    $.ajax({
                        type: "POST",
                        data: formElement.serialize() + '&csrfmiddlewaretoken=' + $('input[name="csrfmiddlewaretoken"]').val(),
                        success: function(response) {
                            if (response.status === 'success') {
                                // Перенаправляем пользователя на страницу staff
                                window.location.href = response.redirect_url;
                            } else {
                                // Обрабатываем ошибки валидации
                                console.error("Ошибка:", response.errors);
                                // Вы можете отображать ошибки на странице здесь
                        }},
                        error: function(xhr, status, error) {
                            console.error("Ошибка:", error);
                        }
                    });
                }
            },
            Отмена: function() {
                console.log("Закрыть нажато");
            }
        }
    });
});