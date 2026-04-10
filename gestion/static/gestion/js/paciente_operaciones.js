// gestion/static/gestion/js/paciente_operaciones.js

// 1. FUNCIÓN SEGURA PARA BUSCAR MODALES (Evita que el JS choque)
function getModal(modalId) {
    const el = document.getElementById(modalId);
    if (!el) return null; // Si no existe en esta pantalla, no hace nada
    return bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
}

// 2. ABRIR MODAL (CREAR O EDITAR PACIENTE)
function abrirModalPaciente(id = null) {
    let url = id ? `/paciente/modal/${id}/` : '/paciente/modal/';

    fetch(url)
        .then(r => r.json())
        .then(data => {
            document.getElementById('contenidoModalPaciente').innerHTML = data.html_form;
            const modal = getModal('modalPaciente');
            if (modal) modal.show();
        })
        .catch(err => console.error("Error al abrir modal paciente:", err));
}

// 3. VIGILANTE GLOBAL DE FORMULARIOS (A prueba de balas)
document.addEventListener('submit', function(event) {
    // Solo atrapamos el formulario si su ID es el de Editar/Crear Paciente
    if (event.target && event.target.id === 'formEditarPaciente') {

        event.preventDefault(); // 🛑 DETIENE LA PANTALLA BLANCA DE JSON

        const form = event.target;
        const formData = new FormData(form);

        // Cambiamos el botón para dar feedback visual
        const btnSubmit = form.querySelector('button[type="submit"]');
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Guardando...';
        }

        fetch(form.action, {
            method: 'POST',
            body: formData
            // Nota: Ya no necesitamos el Token aquí porque viaja oculto en el FormData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                location.reload(); // Éxito: recargamos la página
            } else {
                // Error: Pintamos las letras rojas
                document.getElementById('contenidoModalPaciente').innerHTML = data.html_form;
            }
        })
        .catch(error => {
            console.error("Error fatal:", error);
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = '<i class="fas fa-save me-1"></i> Guardar Cambios';
            }
        });
    }
});

// 4. FUNCIONES DE COBROS (Protegidas por si no existen en la pantalla)
function prepararCobroCita(id, nom, mon) {
    const modal = getModal('modalCobroFicha');
    if (!modal) return;
    document.getElementById('tituloModalCobro').innerText = "Completar Cita";
    document.getElementById('cobroCitaId').value = id;
    document.getElementById('montoCobroFicha').value = parseFloat(mon) || 0;
    modal.show();
}

function prepararCobroGeneral(id, nom, sal) {
    const modal = getModal('modalCobroFicha');
    if (!modal) return;
    document.getElementById('tituloModalCobro').innerText = "Registrar Abono";
    document.getElementById('cobroCitaId').value = "";
    document.getElementById('montoCobroFicha').value = parseFloat(sal) || 0;
    modal.show();
}

function ejecutarCobroFicha() {
    const id = document.getElementById('cobroCitaId').value;
    const url = id ? `/cita/completar/${id}/` : `/pacientes/${CONFIG_PACIENTE.id}/pagos/nuevo/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CONFIG_PACIENTE.csrfToken
        },
        body: JSON.stringify({
            monto: document.getElementById('montoCobroFicha').value,
            metodo: document.getElementById('metodoCobroFicha').value
        })
    })
    .then(r => r.json())
    .then(d => { if(d.status === 'ok') location.reload(); });
}