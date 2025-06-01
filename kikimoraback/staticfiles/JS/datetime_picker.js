// datetime_picker.js

// Инициализация Flatpickr для начала и окончания скидки
flatpickr("#start_datetime", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
    time_24hr: true,
    defaultDate: new Date(),
    minDate: "today",
    minuteIncrement: 1,
    locale: "ru", // Русская локализация
    theme: "material_blue" // Тема Material Blue
});

flatpickr("#end_datetime", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
    time_24hr: true,
    defaultDate: new Date(),
    minDate: "today",
    minuteIncrement: 1,
    locale: "ru", // Русская локализация
    theme: "material_blue" // Тема Material Blue
});
