// gestion/static/gestion/js/calendario.js

document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'es',
        editable: true, // Habilita Drag & Drop y Resize
        selectable: true,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Hoy', month: 'Mes', week: 'Semana', day: 'Día'
        },
        events: CALENDARIO_CONFIG.urlEventos,
        eventDisplay: 'block',

        // 1. REPROGRAMAR (DRAG & DROP)
        eventDrop: function(info) {
            actualizarCita(info.event);
        },

        // 2. AJUSTAR DURACIÓN (RESIZE)
        eventResize: function(info) {
            actualizarCita(info.event);
        },

        // 3. QUICK VIEW (CLICK)
        eventClick: function(info) {
            info.jsEvent.preventDefault(); // Evita navegar si tiene URL
            mostrarQuickView(info.event);
        },

        // 4. NUEVA CITA DESDE GRID
        select: function(info) {
            abrirModalNuevaCita(info.startStr, info.allDay);
        }
    });

    calendar.render();
    window.fullCalendarInstance = calendar; // Para acceso global

    // FILTRO DE DOCTORES
    const doctorFilter = document.getElementById('doctorFilter');
    if (doctorFilter) {
        doctorFilter.addEventListener('change', function() {
            calendar.refetchEvents();
        });
    }

    // Modificamos la carga de eventos para incluir el filtro
    calendar.setOption('eventSources', [
        {
            url: CALENDARIO_CONFIG.urlEventos,
            extraParams: function() {
                return {
                    doctor_id: doctorFilter ? doctorFilter.value : 'all'
                };
            }
        }
    ]);
});

// FUNCIÓN PARA ACTUALIZAR EN DB
function actualizarCita(event) {
    const data = {
        id: event.id,
        start: event.startStr,
        end: event.endStr || event.startStr,
    };

    fetch('/api/citas/reprogramar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CALENDARIO_CONFIG.csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(res => {
        if (res.status !== 'ok') {
            alert("Error al sincronizar: " + res.message);
            window.fullCalendarInstance.refetchEvents();
        }
    })
    .catch(err => {
        console.error(err);
        window.fullCalendarInstance.refetchEvents();
    });
}

// MOSTRAR VISTA RÁPIDA
function mostrarQuickView(event) {
    const modalEl = document.getElementById('modalQuickView');
    const contentEl = document.getElementById('quickViewContent');
    
    const props = event.extendedProps;
    
    contentEl.innerHTML = `
        <div class="bg-gray-900 px-6 py-8 text-white relative overflow-hidden">
            <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl -mr-16 -mt-16"></div>
            <div class="relative z-10 text-center">
                <div class="w-20 h-20 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4 backdrop-blur-md">
                    <i class="fas fa-user text-3xl"></i>
                </div>
                <h3 class="text-xl font-black tracking-tight">${event.title}</h3>
                <p class="text-[10px] uppercase tracking-[0.2em] font-bold text-blue-400 mt-2">${props.tratamiento_nombre || 'Consulta'}</p>
            </div>
        </div>
        <div class="p-8">
            <div class="space-y-4 mb-8">
                <div class="flex items-center gap-4 text-sm">
                    <div class="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center text-gray-400"><i class="far fa-clock"></i></div>
                    <div>
                        <p class="text-[10px] font-black text-gray-400 uppercase">Horario</p>
                        <p class="font-bold text-gray-700">${event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                    </div>
                </div>
                <div class="flex items-center gap-4 text-sm">
                    <div class="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center text-gray-400"><i class="fas fa-notes-medical"></i></div>
                    <div>
                        <p class="text-[10px] font-black text-gray-400 uppercase">Motivo</p>
                        <p class="font-bold text-gray-700 text-xs line-clamp-2">${props.motivo || 'Sin descripción'}</p>
                    </div>
                </div>
            </div>
            <div class="flex flex-col gap-2">
                <a href="${event.url}" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-black py-4 rounded-2xl text-center shadow-lg shadow-blue-500/20 transition-all">
                    VER EXPEDIENTE COMPLETO
                </a>
                <button type="button" class="w-full bg-gray-50 text-gray-400 font-bold py-3 rounded-xl text-xs hover:bg-gray-100 transition-all" data-bs-dismiss="modal">
                    CERRAR
                </button>
            </div>
        </div>
    `;

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

function abrirModalNuevaCita(fechaStr, allDay) {
    const [fecha, hora] = fechaStr.includes('T') ? fechaStr.split('T') : [fechaStr, '08:00'];
    
    const inputFecha = document.getElementById('inputFechaCita');
    const inputHora = document.getElementById('inputHoraCita');
    
    if (inputFecha) inputFecha.value = fecha;
    if (inputHora) inputHora.value = hora.substring(0, 5);
    
    const modalEl = document.getElementById('modalNuevaCitaGeneral');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}