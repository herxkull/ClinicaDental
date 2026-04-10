document.addEventListener("DOMContentLoaded", function() {
    // 1. Configuración de la dentadura (Numeración FDI)
    const arcadaSuperior = [18,17,16,15,14,13,12,11, 21,22,23,24,25,26,27,28];
    const arcadaInferior = [48,47,46,45,44,43,42,41, 31,32,33,34,35,36,37,38];

    let datosOdontograma = {};

    // AQUÍ USAMOS EL PUENTE DESDE HTML
    const pacienteId = CONFIG_ODONTOGRAMA.pacienteId;
    const apiUrl = `/paciente/${pacienteId}/odontograma/api/`;

    let dienteSeleccionado = null;
    let caraSeleccionada = null;
    const modalElement = new bootstrap.Modal(document.getElementById('modalEstadoDiente'));

    // 2. Función para dibujar un Diente SVG
    function crearDienteSVG(numero) {
        return `
        <div class="diente-wrapper" id="wrapper-${numero}">
            <svg class="diente-svg" viewBox="0 0 40 40" data-diente="${numero}">
                <polygon points="0,0 40,0 30,10 10,10" class="cara" data-cara="top" />
                <polygon points="40,0 40,40 30,30 30,10" class="cara" data-cara="right" />
                <polygon points="0,40 40,40 30,30 10,30" class="cara" data-cara="bottom" />
                <polygon points="0,0 0,40 10,30 10,10" class="cara" data-cara="left" />
                <polygon points="10,10 30,10 30,30 10,30" class="cara" data-cara="center" />
            </svg>
            <div class="diente-numero">${numero}</div>
        </div>`;
    }

    const divSuperior = document.getElementById('arcada-superior');
    const divInferior = document.getElementById('arcada-inferior');

    if (divSuperior && divInferior) {
        arcadaSuperior.forEach(num => divSuperior.innerHTML += crearDienteSVG(num));
        arcadaInferior.forEach(num => divInferior.innerHTML += crearDienteSVG(num));
    }

    // 3. Cargar datos desde el Servidor
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            datosOdontograma = data;
            renderizarOdontograma();
        });

    // 4. Aplicar colores
    function renderizarOdontograma() {
        document.querySelectorAll('.diente-svg').forEach(svg => {
            const num = svg.getAttribute('data-diente');
            const wrapper = document.getElementById(`wrapper-${num}`);

            svg.querySelectorAll('.cara').forEach(cara => cara.className.baseVal = 'cara estado-sano');
            wrapper.classList.remove('diente-ausente');

            if (datosOdontograma[num]) {
                if (datosOdontograma[num]['ausente']) {
                    wrapper.classList.add('diente-ausente');
                } else {
                    for (const [cara, estado] of Object.entries(datosOdontograma[num])) {
                        if (cara !== 'ausente') {
                            const polygon = svg.querySelector(`[data-cara="${cara}"]`);
                            if (polygon) polygon.className.baseVal = `cara estado-${estado}`;
                        }
                    }
                }
            }
        });
    }

    // 5. Detectar Clics
    // Usamos delegación de eventos para los elementos creados dinámicamente
    document.addEventListener('click', function(e) {
        if (e.target.classList && e.target.classList.contains('cara')) {
            dienteSeleccionado = e.target.closest('.diente-svg').getAttribute('data-diente');
            caraSeleccionada = e.target.getAttribute('data-cara');

            document.getElementById('modal-diente-id').innerText = dienteSeleccionado;
            document.getElementById('modal-cara-nombre').innerText = caraSeleccionada.toUpperCase();

            modalElement.show();
        }
    });

    // 6. Asignar Estado
    document.querySelectorAll('.btn-estado').forEach(btn => {
        btn.addEventListener('click', function() {
            const estado = this.getAttribute('data-estado');

            if (!datosOdontograma[dienteSeleccionado]) {
                datosOdontograma[dienteSeleccionado] = {};
            }

            if (estado === 'ausente') {
                datosOdontograma[dienteSeleccionado] = { ausente: true };
            } else {
                datosOdontograma[dienteSeleccionado]['ausente'] = false;
                datosOdontograma[dienteSeleccionado][caraSeleccionada] = estado;
            }

            renderizarOdontograma();
            modalElement.hide();
            guardarEnServidor();
        });
    });

    // 7. Guardar en Servidor
    function guardarEnServidor() {
        const badge = document.getElementById('estado-guardado');
        badge.className = "badge bg-warning text-dark";
        badge.innerText = "Guardando...";

        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // AQUÍ USAMOS EL PUENTE DESDE HTML PARA EL TOKEN
                'X-CSRFToken': CONFIG_ODONTOGRAMA.csrfToken
            },
            body: JSON.stringify(datosOdontograma)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                badge.className = "badge bg-success";
                badge.innerText = "Guardado";
                setTimeout(() => { badge.className = "badge bg-light text-dark"; }, 2000);
            }
        });
    }
});