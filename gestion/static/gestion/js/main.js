// gestion/static/gestion/js/main.js

document.addEventListener('DOMContentLoaded', function() {

    // 1. INICIALIZAR TOOLTIPS DE BOOTSTRAP (Globitos de texto flotantes)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. AUTO-CERRAR LAS ALERTAS GLOBALES DESPUÉS DE 4 SEGUNDOS
    setTimeout(function() {
        const alertas = document.querySelectorAll('.alert-auto-dismiss');
        alertas.forEach(function(alerta) {
            // Usamos la API de Bootstrap para cerrarlas con la animación suave
            const bsAlert = new bootstrap.Alert(alerta);
            bsAlert.close();
        });
    }, 4000); // 4000 milisegundos = 4 segundos
});