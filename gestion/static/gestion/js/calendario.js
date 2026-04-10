// gestion/static/gestion/js/calendario.js

document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Hoy', month: 'Mes', week: 'Semana', day: 'Día'
        },
        // Usamos la variable inyectada
        events: CALENDARIO_CONFIG.urlEventos,
        eventDisplay: 'block',

        dateClick: function(info) {
            document.getElementById('inputFechaCita').value = info.dateStr;
            var myModal = new bootstrap.Modal(document.getElementById('modalNuevaCita'));
            myModal.show();
        },

        eventClick: function(info) {
            if (info.event.url) return true;
        }
    });
    calendar.render();
});

// Función para el botón superior "+ Agendar Nueva"
function abrirModalNuevaCita() {
    document.getElementById('inputFechaCita').value = ''; // Limpiamos fecha
    var myModal = new bootstrap.Modal(document.getElementById('modalNuevaCita'));
    myModal.show();
}