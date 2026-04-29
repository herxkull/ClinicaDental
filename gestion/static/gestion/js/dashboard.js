// gestion/static/gestion/js/dashboard.js

let citaIdActual = null;
let modalCobroInstancia = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard JS Loaded");
    console.log("Config Labels:", DASHBOARD_CONFIG.etiquetas);
    console.log("Config Data:", DASHBOARD_CONFIG.datos);

    // 1. MANEJO DE SKELETONS Y GRÁFICO
    const skeleton = document.getElementById('skeleton-grafico');
    const contenedorReal = document.getElementById('contenedor-grafico');
    const canvas = document.getElementById('graficoTratamientos');

    if (DASHBOARD_CONFIG.etiquetas && DASHBOARD_CONFIG.etiquetas.length > 0) {
        if (skeleton) skeleton.classList.add('hidden');
        if (contenedorReal) contenedorReal.classList.remove('hidden');

        if (canvas) {
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: DASHBOARD_CONFIG.etiquetas,
                    datasets: [{
                        data: DASHBOARD_CONFIG.datos,
                        backgroundColor: [
                            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
                        ],
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                font: { size: 11, family: 'Inter' }
                            }
                        }
                    },
                    cutout: '75%'
                }
            });
        }
    } else {
        console.log("No data for chart");
        if (skeleton) {
            skeleton.innerHTML = `
                <div class="text-center py-10">
                    <i class="fas fa-chart-pie text-gray-200 text-5xl mb-3"></i>
                    <p class="text-gray-400 text-xs font-bold uppercase tracking-widest">Sin datos este mes</p>
                </div>
            `;
        }
    }

    // 2. INICIALIZAR MODAL DE COBRO
    const modalEl = document.getElementById('modalCobroCita');
    if (modalEl && typeof bootstrap !== 'undefined') {
        modalCobroInstancia = new bootstrap.Modal(modalEl);
    } else {
        console.warn("Bootstrap or Modal element not found");
    }
});

// 3. FUNCIONES DE COBRO RÁPIDO
function prepararCobro(id, nombre, costo) {
    citaIdActual = id;
    const nombreEl = document.getElementById('nombrePacienteCobro');
    const montoEl = document.getElementById('montoCobro');
    
    if (nombreEl) nombreEl.innerText = nombre;
    if (montoEl) montoEl.value = parseFloat(costo) || 0;
    
    if (modalCobroInstancia) {
        modalCobroInstancia.show();
    } else {
        alert("Error: El sistema de cobro no está listo.");
    }
}

function confirmarCompletarCita() {
    const monto = document.getElementById('montoCobro').value;
    const metodo = document.getElementById('metodoCobro').value;

    if (!monto || monto < 0) {
        alert("Por favor ingresa un monto válido.");
        return;
    }

    const btnSubmit = document.querySelector('#modalCobroCita button[onclick*="confirmar"]');
    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Procesando...';
    }

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
        else {
            alert("Error al procesar el cobro.");
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = 'GUARDAR Y FINALIZAR';
            }
        }
    })
    .catch(err => {
        console.error('Error:', err);
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = 'GUARDAR Y FINALIZAR';
        }
    });
}