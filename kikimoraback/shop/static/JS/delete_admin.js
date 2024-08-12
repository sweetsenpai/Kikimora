$(document).on('click', '#submit-button', function(event) {
    event.preventDefault(); // Предотвратить отправку формы
    console.log("Кнопка нажата");

    // Сохраним ссылку на элемент формы
    var formElement = $(this).closest("form");

    // Создаем диалоговое окно
    $.confirm({
        title: 'Добавление нового сортрудника!',
        content: 'Вы уверены, что хотите отправить форму?\nВы даруете кому-то власть которая и не снилась моему отцу!',
        type: 'green',
        buttons: {
            Создать: {
                text: 'Создать',
                btnClass: 'btn-green',
                action: function() {
                    console.log("Попробовать снова нажать");

                    // Ваш AJAX-запрос здесь
                    $.ajax({
                        type: "POST",
                        url: "/staff/create_new_admin/", // Убедитесь, что вы указываете правильный URL
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