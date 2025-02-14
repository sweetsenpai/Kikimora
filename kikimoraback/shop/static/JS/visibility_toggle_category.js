function toggleVisibilityCategory(category_id) {
    $.ajax({
        url: window.location.origin + `/change_visability_category/${category_id}/`, // Проверьте, что URL корректный
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
        },
        success: function (response) {
            var row = $("#category-" + category_id); // Убедитесь, что у строки есть id 'category-{{ category.category_id }}'
            var button = row.find('button'); // Находим кнопку в строке

            if (response.visibility) {
                button.removeClass('btn-primary').addClass('btn-warning').css('color','#C7253E').text('Убрать из выдачи');
            } else {
                button.removeClass('btn-warning').addClass('btn-primary').css('color','white').text('Вернуть в выдачу');
            }
        },
        error: function () {
            console.error("Ошибка AJAX запроса");
        }
    });
}


// Функция для получения CSRF токена из куки
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
