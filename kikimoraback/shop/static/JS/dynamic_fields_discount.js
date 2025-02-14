document.addEventListener("DOMContentLoaded", function() {
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');
    const productSelect = document.getElementById('product');

    // Fetch categories on page load
    fetch('/api/categories/')
        .then(response => response.json())
        .then(data => {
            data.forEach(category => {
                let option = document.createElement('option');
                option.value = category.category_id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
            });
        });

    // Fetch subcategories when a category is selected
    categorySelect.addEventListener('change', function() {
        const categoryId = this.value;

        fetch(`/api/subcategories/?category=${categoryId}`)
            .then(response => response.json())
            .then(data => {
                subcategorySelect.innerHTML = '<option value="">Выберите...</option>'; // Clear previous options
                productSelect.innerHTML = '<option value="">Выберите...</option>'; // Clear previous options
                data.forEach(subcategory => {
                    let option = document.createElement('option');
                    option.value = subcategory.subcategory_id;
                    option.textContent = subcategory.name;
                    subcategorySelect.appendChild(option);
                });
            });
    });

    // Fetch products when a subcategory is selected
    subcategorySelect.addEventListener('change', function() {
        const subcategoryId = this.value;

        fetch(`/api/products/?subcategory=${subcategoryId}`)
            .then(response => response.json())
            .then(data => {
                productSelect.innerHTML = '<option value="">Выберите...</option>'; // Clear previous options
                data.forEach(product => {
                    let option = document.createElement('option');
                    option.value = product.product_id;
                    option.textContent = product.name;
                    productSelect.appendChild(option);
                });
            });
    });
});
