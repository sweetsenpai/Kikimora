function toggleEditMode() {
    const inputs = document.querySelectorAll('#product-form .form-control, #product-form .form-select');
    const displays = document.querySelectorAll('#product-form .input-group span, #product-form img');
    const editButton = document.getElementById('edit-button');
    const saveButton = document.getElementById('save-button');

    // Переключение видимости полей ввода и текстовых отображений
    inputs.forEach(input => {
        if (input.classList.contains('d-none')) {
            const displayId = input.id.replace('-input', '-display').replace('-select', '-display');
            const display = document.getElementById(displayId);
            if (display) {
                let value = display.textContent.trim();

                if (input.tagName === 'SELECT') {
                    // Для выпадающего списка выбираем соответствующий option
                    const selectedOption = Array.from(input.options).find(option => option.text === value);
                    if (selectedOption) {
                        selectedOption.selected = true;
                    }
                } else if (input.type === 'number') {
                    // Заменяем запятую на точку для чисел
                    value = value.replace(',', '.');
                    // Удаление всех символов, кроме цифр, точки или минуса
                    value = value.replace(/[^\d.-]/g, '');
                } else if (input.type === 'text' && input.name === 'photo_url') {
                    value = display.src || value;  // Для URL используйте src изображения
                }

                input.value = value;
            }
        }
        input.classList.toggle('d-none');
    });

    displays.forEach(display => display.classList.toggle('d-none'));

    // Переключение видимости кнопок
    editButton.classList.toggle('d-none');
    saveButton.classList.toggle('d-none');
}