document.addEventListener("DOMContentLoaded", function() {
    const subcategorySelect = document.getElementById('subcategory');
    const productSelect = document.getElementById('product');

    // Загружаем подкатегории при загрузке страницы
    fetch('/api/v1/menu/subcategory/')
        .then(response => response.json())
        .then(data => {
            subcategorySelect.innerHTML = '<option value="">Выберите...</option>'; // Очищаем перед добавлением
            data.forEach(subcategory => {
                let option = document.createElement('option');
                option.value = subcategory.subcategory_id;
                option.textContent = subcategory.name;
                subcategorySelect.appendChild(option);
            });
        })
        .catch(error => console.error('Ошибка загрузки подкатегорий:', error));

    // Загружаем продукты при выборе подкатегории
    subcategorySelect.addEventListener('change', function() {
        const subcategoryId = this.value;

        if (!subcategoryId) {
            productSelect.innerHTML = '<option value="">Выберите...</option>'; // Если ничего не выбрано
            return;
        }

        fetch(`/api/v1/menu/discount_product_menu/${subcategoryId}/`)
            .then(response => response.json())
            .then(data => {
                productSelect.innerHTML = '<option value="">Выберите...</option>'; // Очищаем перед добавлением
                data.forEach(product => {
                    let option = document.createElement('option');
                    option.value = product.product_id;
                    option.textContent = product.name;
                    productSelect.appendChild(option);
                });
            })
            .catch(error => console.error('Ошибка загрузки продуктов:', error));
    });
});
