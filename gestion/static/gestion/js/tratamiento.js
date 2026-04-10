// gestion/static/gestion/js/tratamientos.js

/**
 * Agrega una nueva fila de selección de material (producto y cantidad)
 * al contenedor especificado.
 */
function agregarMaterial(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'row mb-2';

    // Construimos las opciones del <select> leyendo el array de productos
    // que nos pasó Django a través de la variable global TRATAMIENTOS_CONFIG
    let opcionesHTML = '<option value="">Seleccione un producto del inventario...</option>';

    TRATAMIENTOS_CONFIG.productos.forEach(p => {
        opcionesHTML += `<option value="${p.id}">${p.nombre} (Stock: ${p.stock})</option>`;
    });

    // Inyectamos el HTML de la nueva fila
    div.innerHTML = `
        <div class="col-7">
            <select name="producto_id[]" class="form-select" required>
                ${opcionesHTML}
            </select>
        </div>
        <div class="col-3">
            <input type="number" name="cantidad[]" class="form-control" placeholder="Cant." min="1" required>
        </div>
        <div class="col-2">
            <button type="button" class="btn btn-outline-danger w-100" onclick="this.parentElement.parentElement.remove()" title="Eliminar fila">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;

    container.appendChild(div);
}