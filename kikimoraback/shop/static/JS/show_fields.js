$(document).ready(function() {
    // Обработчик изменений для радиокнопок типа промокода
    $('input[name="type"]').on('change', function() {
        // Скрыть все поля сначала
        $('#discount-fields').hide();
        $('#product-fields').hide();

        // Проверяем выбранное значение
        const type = $('input[name="type"]:checked').val();

        if (type === 'cart_discount' || type === 'product_discount') {
            $('#discount-fields').show();
        }

        if (type === 'product_discount') {
            $('#product-fields').show();
        }
    });
});
