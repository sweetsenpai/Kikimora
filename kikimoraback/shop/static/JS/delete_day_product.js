$(document).ready(function() {
    // Обработчик нажатия на кнопку "Удалить"
    $('.delete-day-product').on('click', function() {
        const productId = $(this).val(); // Получаем productId из значения кнопки
        const row = $(this).closest('tr'); // Находим строку таблицы, которая содержит эту кнопку

        if (confirm('Вы уверены, что хотите удалить этот товар дня?')) {
            $.ajax({
                url: `/api/v1/delete_day_product/${productId}/`,
                type: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                success: function(response) {
                    if (response.status === 'success') {
                        row.fadeOut(); // Удаляем строку из таблицы
                        alert('Товар дня удален.');
                    } else {
                        alert(response.message || 'Ошибка при удалении товара дня.');
                    }
                },
                error: function(xhr) {
                    alert('Ошибка при удалении товара дня.');
                }
            });
        }
    });
});

// Функция для получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Проверяем, начинается ли cookie с нужного имени
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
