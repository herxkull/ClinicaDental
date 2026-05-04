// gestion/static/gestion/js/calendario.js

document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'es',
        editable: true, // Habilita Drag & Drop y Resize
        selectable: true,
        dayMaxEvents: 3, // limita los eventos por celda para que no se desborden
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Hoy', month: 'Mes', week: 'Semana', day: 'Día'
        },
        eventDisplay: 'block',

        // 1. FUENTE DE EVENTOS CON FILTRO
        events: function(info, successCallback, failureCallback) {
            const doctorFilter = document.getElementById('doctorFilter');
            const docId = doctorFilter ? doctorFilter.value : 'all';
            
            // Construir la URL con parámetros
            let url = CALENDARIO_CONFIG.urlEventos + '?doctor_id=' + encodeURIComponent(docId);
            if (info.startStr) url += '&start=' + encodeURIComponent(info.startStr);
            if (info.endStr) url += '&end=' + encodeURIComponent(info.endStr);

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    successCallback(data);
                })
                .catch(error => {
                    console.error('Error al cargar eventos:', error);
                    failureCallback(error);
                });
        },

        // 2. REPROGRAMAR (DRAG & DROP)
        eventDrop: function(info) {
            actualizarCita(info.event);
        },

        // 3. AJUSTAR DURACIÓN (RESIZE)
        eventResize: function(info) {
            actualizarCita(info.event);
        },

        // 4. QUICK VIEW (CLICK)
        eventClick: function(info) {
            info.jsEvent.preventDefault(); // Evita navegar si tiene URL
            mostrarQuickView(info.event);
        },

        // 5. NUEVA CITA DESDE GRID
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
    if (!props || !props.cita_id) {
        contentEl.innerHTML = `
            <div class="bg-gray-900 px-6 py-8 text-white text-center">
                <h3 class="text-xl font-black">${event.title}</h3>
                <p class="text-[10px] text-gray-400 mt-2">${props ? (props.tratamiento_nombre || 'Evento') : 'Evento'}</p>
            </div>
            <div class="p-8">
                <button type="button" class="w-full bg-gray-50 text-gray-400 font-bold py-3 rounded-xl text-xs hover:bg-gray-100 transition-all" data-bs-dismiss="modal">
                    CERRAR
                </button>
            </div>
        `;
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
        return;
    }

    const badgeClass = props.badge_class || 'bg-blue-500';

    contentEl.innerHTML = `
        <div class="bg-gray-900 px-6 py-8 text-white relative overflow-hidden">
            <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl -mr-16 -mt-16"></div>
            <div class="relative z-10 text-center">
                <div class="inline-flex mb-3 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${badgeClass}">
                    ${props.estado_display || 'Pendiente'}
                </div>
                <div class="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-3 backdrop-blur-md">
                    <i class="fas fa-user text-2xl"></i>
                </div>
                <h3 class="text-lg font-black tracking-tight">${event.title}</h3>
                <p class="text-[10px] uppercase tracking-[0.2em] font-bold text-blue-400 mt-1">${props.tratamiento_nombre || 'Consulta'}</p>
            </div>
        </div>
        <div class="p-6 bg-white">
            <div class="space-y-4 mb-6">
                <!-- Horario y Motivo -->
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

            <!-- ACTION BAR (Recordatorios rápidos) -->
            <div class="flex items-center gap-2 mb-6 bg-gray-50/50 p-3 rounded-2xl border border-gray-100 justify-around">
                <a href="https://wa.me/${props.paciente_telefono ? props.paciente_telefono.replace(/\s+/g, '') : ''}" target="_blank"
                   class="w-12 h-12 bg-green-50 text-green-500 rounded-xl flex items-center justify-center hover:bg-green-100 transition-all"
                   title="WhatsApp">
                    <i class="fab fa-whatsapp text-xl"></i>
                </a>
                <a href="${event.url}" class="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center hover:bg-blue-100 transition-all"
                   title="Ir al Expediente">
                    <i class="fas fa-folder-open text-xl"></i>
                </a>
            </div>

            <!-- SELECTOR DE ESTADO -->
            <form id="formCambiarEstado" class="space-y-4 mb-6">
                <div>
                    <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 block">Cambiar Estado</label>
                    <select id="selectNuevoEstado" class="w-full bg-gray-50 border border-gray-100 rounded-2xl py-3 px-4 text-xs font-black text-gray-700 focus:ring-4 focus:ring-blue-500/10 transition-all cursor-pointer">
                        <option value="PROGRAMADA" ${props.estado === 'PROGRAMADA' ? 'selected' : ''}>Programada</option>
                        <option value="PENDIENTE" ${props.estado === 'PENDIENTE' ? 'selected' : ''}>Pendiente</option>
                        <option value="CONFIRMADA" ${props.estado === 'CONFIRMADA' ? 'selected' : ''}>Confirmada</option>
                        <option value="EN_SALA" ${props.estado === 'EN_SALA' ? 'selected' : ''}>En Sala (Esperando)</option>
                        <option value="EN_CURSO" ${props.estado === 'EN_CURSO' ? 'selected' : ''}>En Curso</option>
                        <option value="COMPLETADA" ${props.estado === 'COMPLETADA' ? 'selected' : ''}>Completada</option>
                        <option value="CANCELADA" ${props.estado === 'CANCELADA' ? 'selected' : ''}>Cancelada</option>
                        <option value="REPROGRAMADA" ${props.estado === 'REPROGRAMADA' ? 'selected' : ''}>Reprogramada</option>
                        <option value="NO_ASISTIO" ${props.estado === 'NO_ASISTIO' ? 'selected' : ''}>No Asistió</option>
                    </select>
                </div>

                <!-- Input Dinámico para Motivo de Cancelación/No Asistencia -->
                <div id="divMotivo" class="hidden">
                    <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 block">Motivo / Notas</label>
                    <input type="text" id="inputMotivoEstado" class="w-full bg-gray-50 border border-gray-100 rounded-2xl py-3 px-4 text-xs font-bold text-gray-700 focus:ring-4 focus:ring-blue-500/10 transition-all" placeholder="Ej: No pudo asistir...">
                </div>

                <!-- Input Dinámico para Reprogramada -->
                <div id="divReprogramacion" class="hidden grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 block">Nueva Fecha</label>
                        <input type="date" id="inputFechaReprog" class="w-full bg-gray-50 border border-gray-100 rounded-2xl py-3 px-3 text-xs font-bold text-gray-700 focus:ring-4 focus:ring-blue-500/10 transition-all">
                    </div>
                    <div>
                        <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 block">Nueva Hora</label>
                        <input type="time" id="inputHoraReprog" class="w-full bg-gray-50 border border-gray-100 rounded-2xl py-3 px-3 text-xs font-bold text-gray-700 focus:ring-4 focus:ring-blue-500/10 transition-all">
                    </div>
                </div>

                <button type="submit" id="btnGuardarEstado" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-black py-4 rounded-3xl text-center shadow-lg shadow-blue-500/20 transition-all uppercase tracking-wide text-xs">
                    Actualizar Estado
                </button>
            </form>

            <button type="button" class="w-full bg-gray-50 text-gray-400 font-bold py-3 rounded-xl text-xs hover:bg-gray-100 transition-all" data-bs-dismiss="modal">
                CERRAR
            </button>
        </div>
    `;

    const selectEl = document.getElementById('selectNuevoEstado');
    const divMotivo = document.getElementById('divMotivo');
    const divReprog = document.getElementById('divReprogramacion');

    selectEl.addEventListener('change', function(e) {
        const val = e.target.value;
        if (val === 'CANCELADA' || val === 'NO_ASISTIO') {
            divMotivo.classList.remove('hidden');
            divReprog.classList.add('hidden');
        } else if (val === 'REPROGRAMADA') {
            divMotivo.classList.add('hidden');
            divReprog.classList.remove('hidden');
        } else {
            divMotivo.classList.add('hidden');
            divReprog.classList.add('hidden');
        }
    });

    if (props.estado === 'CANCELADA' || props.estado === 'NO_ASISTIO') {
        divMotivo.classList.remove('hidden');
    } else if (props.estado === 'REPROGRAMADA') {
        divReprog.classList.remove('hidden');
    }

    document.getElementById('formCambiarEstado').addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = document.getElementById('btnGuardarEstado');
        const originalText = btn.innerHTML;
        const nuevo_estado = selectEl.value;

        const formData = new FormData();
        formData.append('nuevo_estado', nuevo_estado);
        formData.append('motivo', document.getElementById('inputMotivoEstado').value || '');
        formData.append('fecha', document.getElementById('inputFechaReprog').value || '');
        formData.append('hora', document.getElementById('inputHoraReprog').value || '');

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESANDO...';

            const response = await fetch(`/api/citas/${props.cita_id}/cambiar-estado/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': CALENDARIO_CONFIG.csrfToken },
                body: formData
            });

            const result = await response.json();
            if (result.status === 'success') {
                bootstrap.Modal.getInstance(modalEl).hide();
                
                if (nuevo_estado === 'COMPLETADA' && typeof window.abrirCheckout === 'function') {
                    window.abrirCheckout(
                        props.cita_id, 
                        props.paciente_nombre || 'Paciente', 
                        props.tratamiento_precio || 0, 
                        props.tratamiento_nombre || 'Consulta'
                    );
                } else {
                    Swal.fire({
                        title: 'Estado Actualizado',
                        text: `El estado ha sido cambiado a ${result.nuevo_estado}`,
                        icon: 'success',
                        timer: 2000,
                        timerProgressBar: true,
                        customClass: { popup: 'rounded-[2rem]' }
                    }).then(() => {
                        if (window.fullCalendarInstance) {
                            window.fullCalendarInstance.refetchEvents();
                        } else {
                            window.location.reload();
                        }
                    });
                }
            } else {
                throw new Error(result.message || 'Error desconocido');
            }
        } catch (error) {
            Swal.fire({
                title: 'Error',
                text: error.message,
                icon: 'error',
                confirmButtonColor: '#ef4444',
                customClass: { popup: 'rounded-[2rem]' }
            });
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });

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