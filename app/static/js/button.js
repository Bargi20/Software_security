$('.order').click(function (e) {
    let button = $(this);
    let form = button.closest('form');
    
    // Controlla se tutti i campi required sono compilati
    let allFieldsFilled = true;
    form.find('input[required]').each(function() {
        if (!$(this).val() || $(this).val().trim() === '') {
            allFieldsFilled = false;
            return false; // break the loop
        }
    });
    
    // Avvia l'animazione solo se tutti i campi sono compilati
    if (allFieldsFilled && !button.hasClass('animate')) {
        button.addClass('animate');
        setTimeout(() => {
            button.removeClass('animate');
        }, 10000);
    }
});