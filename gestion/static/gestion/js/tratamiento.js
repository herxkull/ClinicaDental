// gestion/static/gestion/js/tratamientos.js

/**
 * Agrega una nueva fila de selección de material (producto y cantidad)
 */
function agregarMaterial(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'flex gap-3 fila-material animate-in fade-in slide-in-from-top-2 duration-300';

    let opcionesHTML = '<option value="">Seleccione un producto...</option>';
    TRATAMIENTOS_CONFIG.productos.forEach(p => {
        opcionesHTML += `<option value="${p.id}" data-costo="${p.costo}">${p.nombre} ($${p.costo})</option>`;
    });

    div.innerHTML = `
        <div class="flex-grow">
            <select name="producto_id" class="w-full px-5 py-3 bg-white border border-gray-100 rounded-xl font-medium text-sm select2-insumo-dinamico" onchange="actualizarCalculos(this)" required>
                ${opcionesHTML}
            </select>
        </div>
        <div class="w-24">
            <input type="number" name="cantidad" value="1" 
                   class="w-full px-4 py-3 bg-white border border-gray-100 rounded-xl text-center font-bold text-sm" 
                   min="1" oninput="actualizarCalculos(this)" required>
        </div>
        <button type="button" onclick="this.parentElement.remove(); actualizarCalculos(document.getElementById('${containerId}'));" 
                class="w-12 h-12 flex items-center justify-center text-red-400 hover:bg-red-50 rounded-xl transition-colors">
            <i class="fas fa-trash-alt"></i>
        </button>
    `;

    container.appendChild(div);
    
    // Inicializar Select2 en el nuevo elemento si jQuery está disponible
    if (typeof $ !== 'undefined') {
        $(div).find('.select2-insumo-dinamico').select2({
            placeholder: "Buscar insumo...",
            dropdownParent: $(container).closest('.modal')
        });
    }

    actualizarCalculos(container);
}

/**
 * Calcula el costo total y margen en tiempo real dentro del modal
 */
function actualizarCalculos(element) {
    const modal = element.closest('.modal-content');
    if (!modal) return;

    const precioVenta = parseFloat(modal.querySelector('.input-precio').value) || 0;
    let costoTotal = 0;

    const filas = modal.querySelectorAll('.contenedor-materiales .fila-material');
    
    filas.forEach(fila => {
        const select = fila.querySelector('select');
        const cantidadInput = fila.querySelector('input[name="cantidad"]');
        const cantidad = parseFloat(cantidadInput.value) || 0;
        
        // Obtener costo desde el select (Select2 o estándar)
        let costoUnitario = 0;
        const selectedOption = select.options[select.selectedIndex];
        
        if (selectedOption && selectedOption.value) {
            // Buscamos en el config por si el data-costo no está disponible en Select2 clonado
            const prodId = parseInt(selectedOption.value);
            const producto = TRATAMIENTOS_CONFIG.productos.find(p => p.id === prodId);
            if (producto) costoUnitario = producto.costo;
        }

        costoTotal += (costoUnitario * cantidad);
    });

    // Actualizar Badges
    const badgeCosto = modal.querySelector('.badge-costo');
    const badgeMargen = modal.querySelector('.badge-margen');

    if (badgeCosto) {
        badgeCosto.innerText = `Costo Insumos: $${costoTotal.toFixed(2)}`;
    }

    if (badgeMargen) {
        const ganancia = precioVenta - costoTotal;
        const roi = precioVenta > 0 ? (ganancia / precioVenta) * 100 : 0;
        
        badgeMargen.innerText = `ROI: ${roi.toFixed(0)}%`;
        
        // Colores dinámicos
        if (roi > 50) {
            badgeMargen.className = 'text-[10px] font-bold text-green-600 bg-white px-2 py-1 rounded-lg border border-green-100 badge-margen';
        } else if (roi < 30) {
            badgeMargen.className = 'text-[10px] font-bold text-red-600 bg-white px-2 py-1 rounded-lg border border-red-100 badge-margen';
        } else {
            badgeMargen.className = 'text-[10px] font-bold text-amber-600 bg-white px-2 py-1 rounded-lg border border-amber-100 badge-margen';
        }
    }
}

// Escuchar cambios en el precio base para recalcular margen
document.querySelectorAll('.input-precio').forEach(input => {
    input.addEventListener('input', function() {
        actualizarCalculos(this);
    });
});