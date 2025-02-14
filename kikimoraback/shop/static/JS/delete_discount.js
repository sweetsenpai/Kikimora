$(document).on('click', '#submit-button', function(event) {
    event.preventDefault(); // Предотвратить отправку формы
    console.log("Кнопка нажата");

    var formElement = $(this).closest("form");

    $.confirm({
        title: 'Удаление скидки',
        content: 'Вы уверены, что хотите удалить эту скидку?\nСомневаюсь, что после удаления мы сможем всё исправить если Вы передумаете!',
        type: 'red',
        buttons: {
            Удалить: {
                text: 'Удалить',
                btnClass: 'btn-red',
                action: function() {
                    console.log("Попробовать снова нажать");

                    $.ajax({
                        type: "POST",
                        url: formElement.attr('action'),  // Используем URL из атрибута action формы
                        data: formElement.serialize(),
                        success: function(response) {
                            if (response.status === 'success') {
                                window.location.href = '/discounts';  // Перенаправляем пользователя на /discounts
                            } else {
                                console.error("Ошибка:", response.errors);
                            }
                        },
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
