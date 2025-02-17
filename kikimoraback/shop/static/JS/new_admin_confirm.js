$(document).on('click', '#submit-button', function(event) {
    event.preventDefault(); // Предотвратить отправку формы
    console.log("Кнопка нажата");

    // Сохраним ссылку на элемент формы
    var formElement = $(this).closest("form");

    // Создаем диалоговое окно
    $.confirm({
        title: 'Добавление нового сотрудника!',
        content: 'Вы уверены, что хотите отправить форму?',
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
                        url: "/apanel/staff/create_new_admin/",
                        data: formElement.serialize() + '&csrfmiddlewaretoken=' + $('input[name="csrfmiddlewaretoken"]').val(),
                        success: function(response) {
                            console.log("Ответ от сервера:", response);
                            if (response.status === 'success') {
                                window.location.href = response.redirect_url;
                            } else {
                                console.error("Ошибка:", response.errors);

                                // Очищаем предыдущие ошибки
                                $('#errorContainer').html('');

                                const errors = response.errors;
                                let hasErrors = false; // Флаг, указывающий на наличие ошибок

                                for (const field in errors) {
                                    $('#errorContainer').append(`<p>${field}: ${errors[field]}</p>`);
                                    hasErrors = true; // Устанавливаем флаг, если есть хотя бы одна ошибка
                                }

                                // Показать или скрыть #errorContainer в зависимости от наличия ошибок
                                if (hasErrors) {
                                    $('#errorContainer').show(); // Показываем контейнер
                                } else {
                                    $('#errorContainer').hide(); // Скрываем контейнер
                                }
                            }
                        } ,
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