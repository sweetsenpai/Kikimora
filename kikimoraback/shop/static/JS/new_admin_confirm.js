function confirmForm() {
    if (confirm("Вы уверены, что хотите отправить форму?\nВы даруете кому-то власть которая и не снилась моему отцу!")) {
        // Отправляем форму на сервер
        $.ajax({
            type: "POST",
            data: {
                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
                form_data: $(this).closest("form").serialize()
            },
            success: function(response) {
                 console.log(response)
            }
        });
    } else {
        return false;
    }
}
