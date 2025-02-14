$(document).on('click', '.stop-discount', function(event) {
    event.preventDefault();

    var discountId = $(this).data('discount-id');
    var button = $(this);

    $.ajax({
        type: 'POST',
        url: '/api/discounts/stop/' + discountId + '/',
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        success: function(response) {
            if (response.status === 'success') {
                button.closest('tr').find('td:nth-child(6)').text('Остановлено');
                button.remove(); // Удаляем кнопку после успешного обновления
            } else {
                console.error("Ошибка:", response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error("Ошибка:", error);
        }
    });
});
