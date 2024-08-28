function toggleVisibilityProduct(product_id) {
    $.ajax({
        url: window.location.origin + `/change_visibility_product/${product_id}/`,
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
        },
        success: function (response) {
            var row = $("#product-" + product_id);
            var button = row.find('button');

            if (response.visibility) {
                button.removeClass('btn-primary').addClass('btn-warning').css('color','#C7253E').text('Убрать из выдачи');
            } else {
                button.removeClass('btn-warning').addClass('btn-primary').css('color','white').text('Вернуть в выдачу');
            }
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
