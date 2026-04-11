// gestion/static/gestion/js/paciente_operaciones.js

// 1. FUNCIÓN SEGURA PARA BUSCAR MODALES
function getModal(modalId) {
    const el = document.getElementById(modalId);
    if (!el) return null;
    return bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
}

// 2. ABRIR MODAL PACIENTE
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

// 2.5 ABRIR MODAL CITA (¡NUEVO!)
// Recibe la URL directamente desde el botón HTML para no fallar nunca
function abrirModalCita(url_vista) {
    fetch(url_vista)
        .then(r => r.json())
        .then(data => {
            document.getElementById('contenidoModalCita').innerHTML = data.html_form;
            const modal = getModal('modalCita');
            if (modal) modal.show();
        })
        .catch(err => console.error("Error al abrir modal cita:", err));
}

// 3. VIGILANTE GLOBAL DE FORMULARIOS (Mejorado para atrapar múltiples modales)
document.addEventListener('submit', function(event) {
    // AHORA ATRAPA TANTO EL PACIENTE COMO LA CITA
    if (event.target && (event.target.id === 'formEditarPaciente' || event.target.id === 'form-cita-modal')) {

        event.preventDefault(); // 🛑 DETIENE LA PANTALLA BLANCA

        const form = event.target;
        const formData = new FormData(form);

        const btnSubmit = form.querySelector('button[type="submit"]');
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Guardando...';
        }

        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                location.reload();
            } else {
                // Inyecta los errores rojos en la caja correcta según el formulario
                if (form.id === 'formEditarPaciente') {
                    document.getElementById('contenidoModalPaciente').innerHTML = data.html_form;
                } else if (form.id === 'form-cita-modal') {
                    document.getElementById('contenidoModalCita').innerHTML = data.html_form;
                }
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

// 4. FUNCIONES DE COBROS
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