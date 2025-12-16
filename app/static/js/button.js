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
    
    // Se tutti i campi sono compilati e l'animazione non è già in corso
    if (allFieldsFilled && !button.hasClass('animate')) {
        // Previeni il submit immediato del form
        e.preventDefault();
        
        // Avvia l'animazione
        button.addClass('animate');
        
        // Dopo 10 secondi (quando l'animazione finisce), fai il submit del form
        // NON rimuovo la classe animate per mantenere visibile "Codice verificato" / "Accesso effettuato"
        setTimeout(() => {
            // Submit del form direttamente senza rimuovere animate
            form.off('submit').submit();
        }, 4000);
    }
});