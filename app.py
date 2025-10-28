import pandas as pd
from flask import Flask, render_template, request

# Importa tus funciones desde la carpeta 'funciones'
from funciones.generarDatos import generar_dataset
from funciones.crearCubo import cubo_base
from funciones.operacionesCubo import (
    pivot_anio_region,
    dice_subset,
    drilldown_producto_region # Usaremos esta para el drill-through
)

# --- Configuración de la App ---
app = Flask(__name__)

# --- Carga de Datos Global ---
# Cargamos los datos una sola vez al iniciar el servidor
print("Cargando dataset...")
df = generar_dataset(seed=42)
print("Dataset cargado.")

# Opciones para los menús desplegables (calculadas una vez)
TODOS_ANIOS = sorted(df['Año'].unique())
TODOS_TRIMESTRES = sorted(df['Trimestre'].unique())
TODOS_PRODUCTOS = sorted(df['Producto'].unique())
TODAS_REGIONES = sorted(df['Región'].unique())

# --- Formateador de números para las tablas HTML ---
# Esto hace que los números se vean bien (ej. 1,234.56)
pd.set_option('display.float_format', '{:,.2f}'.format)


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Ruta principal que maneja toda la lógica del punto (c).
    """
    
    # --- c.iii) Cubo Completo (Siempre se muestra) ---
    cubo = cubo_base(df)
    # Convertimos el DataFrame a HTML, dándole una clase CSS
    html_cubo_completo = cubo.to_html(classes='tabla-olap', na_rep='-')

    # --- c.i) Una Cara del Cubo (Pivot) (Siempre se muestra) ---
    piv = pivot_anio_region(df)
    html_cara_cubo = piv.to_html(classes='tabla-olap', na_rep='-')

    # --- Valores por defecto para los formularios ---
    # Sección (Dice)
    sel_seccion = {
        'anios': [2024, 2025],
        'regiones': ['Norte', 'Sur']
    }
    # Drill-Through
    sel_drill = {
        'anio': 2024,
        'trim': 1,
        'prod': 'A',
        'reg': 'Norte'
    }

    # --- Procesamiento de Formularios (si se envía uno) ---
    if request.method == 'POST':
        # Identificamos qué formulario se envió
        form_name = request.form.get('form_name')
        
        if form_name == 'seccion':
            # c.ii) Actualizar valores de SECCIÓN
            sel_seccion['anios'] = [int(a) for a in request.form.getlist('seccion_anios')]
            sel_seccion['regiones'] = request.form.getlist('seccion_regiones')
        
        elif form_name == 'drill':
            # c.iv) Actualizar valores de DRILL-THROUGH
            sel_drill['anio'] = int(request.form.get('drill_anio'))
            sel_drill['trim'] = int(request.form.get('drill_trim'))
            sel_drill['prod'] = request.form.get('drill_prod')
            sel_drill['reg'] = request.form.get('drill_reg')

    # --- c.ii) Lógica de la Sección (Dice) ---
    df_seccion = dice_subset(
        df,
        anios=sel_seccion['anios'],
        regiones=sel_seccion['regiones']
    )
    # Creamos la vista agregada de esa sección
    vista_seccion = pd.pivot_table(
        df_seccion,
        values="Ventas",
        index=["Producto", "Canal"],
        columns=["Año", "Región"],
        aggfunc="sum",
        margins=True,
        margins_name="Total"
    )
    html_seccion = vista_seccion.to_html(classes='tabla-olap', na_rep='-')

    # --- c.iv) Lógica de Datos de Celda (Drill-Through) ---
    # Usamos 'dice' para encontrar los registros exactos
    df_datos_celda = dice_subset(
        df,
        anios=[sel_drill['anio']],
        regiones=[sel_drill['reg']],
        productos=[sel_drill['prod']]
    )
    # Filtramos por trimestre (dice_subset no lo incluye)
    df_datos_celda = df_datos_celda[
        df_datos_celda["Trimestre"] == sel_drill['trim']
    ].copy()
    html_drill = df_datos_celda.to_html(classes='tabla-datos-crudos', index=False)


    # --- Renderizar el Template ---
    # Pasamos todas las variables al archivo index.html
    return render_template(
        'index.html',
        # Tablas HTML
        html_cubo_completo=html_cubo_completo,
        html_cara_cubo=html_cara_cubo,
        html_seccion=html_seccion,
        html_drill=html_drill,
        # Opciones para los <select> y checkboxes
        opciones={
            'anios': TODOS_ANIOS,
            'trimestres': TODOS_TRIMESTRES,
            'productos': TODOS_PRODUCTOS,
            'regiones': TODAS_REGIONES
        },
        # Valores seleccionados para repoblar los formularios
        sel_seccion=sel_seccion,
        sel_drill=sel_drill
    )


if __name__ == "__main__":
    # Inicia el servidor en modo de depuración
    app.run(debug=True)