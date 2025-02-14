function toggleEditMode() {
    const inputs = document.querySelectorAll('#product-form .form-control');
    const displays = document.querySelectorAll('#product-form .input-group span, #product-form img');
    const editButton = document.getElementById('edit-button');
    const saveButton = document.getElementById('save-button');

    inputs.forEach(input => {
        if (input.classList.contains('d-none')) {
            const display = document.querySelector(`#${input.id.replace('-input', '-display')}`);
            if (display) {
                let value = display.textContent.trim();

                if (input.type === 'number') {
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
    editButton.classList.toggle('d-none');
    saveButton.classList.toggle('d-none');
}
