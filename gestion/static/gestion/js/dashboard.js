// gestion/static/gestion/js/dashboard.js

let citaIdActual = null;
let modalCobroInstancia = null;

document.addEventListener('DOMContentLoaded', function() {
    // 1. INICIALIZAR GRÁFICO (Usa las variables inyectadas desde Django)
    if (DASHBOARD_CONFIG.etiquetas.length > 0) {
        const ctx = document.getElementById('graficoTratamientos').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: DASHBOARD_CONFIG.etiquetas,
                datasets: [{
                    label: 'Citas',
                    data: DASHBOARD_CONFIG.datos,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. INICIALIZAR MODAL DE COBRO
    const modalEl = document.getElementById('modalCobroCita');
    if (modalEl) {
        modalCobroInstancia = new bootstrap.Modal(modalEl);
    }
});

// 3. FUNCIONES DE COBRO RÁPIDO
function prepararCobro(id, nombre, costo) {
    citaIdActual = id;
    document.getElementById('nombrePacienteCobro').innerText = nombre;
    document.getElementById('montoCobro').value = parseFloat(costo) || 0;
    modalCobroInstancia.show();
}

function confirmarCompletarCita() {
    const monto = document.getElementById('montoCobro').value;
    const metodo = document.getElementById('metodoCobro').value;

    if (!monto || monto < 0) {
        alert("Por favor ingresa un monto válido.");
        return;
    }

    // Cambiar botón a cargando
    const btnSubmit = document.querySelector('#modalCobroCita .btn-primary');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Procesando...';

    fetch(`/cita/completar/${citaIdActual}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': DASHBOARD_CONFIG.csrfToken
        },
        body: JSON.stringify({ monto: monto, metodo: metodo })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'ok') location.reload();
        else alert("Error al procesar el cobro.");
    })
    .catch(err => {
        console.error('Error:', err);
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = 'GUARDAR Y FINALIZAR';
    });
}