import pandas as pd
from flask import Flask, render_template, request

# Importa tus funciones (sin cambios aquí)
from funciones.generarDatos import generar_dataset
from funciones.crearCubo import cubo_base
from funciones.operacionesCubo import pivot_anio_region, dice_subset

# --- Configuración y Carga de Datos (Sin cambios) ---
app = Flask(__name__)
print("Cargando dataset...")
df = generar_dataset(seed=42)
print("Dataset cargado.")

# Opciones globales para los menús desplegables
TODOS_ANIOS = sorted(df['Año'].unique())
TODOS_TRIMESTRES = sorted(df['Trimestre'].unique())
TODOS_PRODUCTOS = sorted(df['Producto'].unique())
TODAS_REGIONES = sorted(df['Región'].unique())

pd.set_option('display.float_format', '{:,.2f}'.format)

# --- Definición de Rutas (La Gran Mejora) ---

@app.route('/')
def index():
    """Ruta 'Home': Muestra la página de bienvenida y navegación."""
    # 'active_page' le dirá a la barra de navegación qué botón resaltar
    return render_template('index.html', active_page='home')

@app.route('/cubo-completo')
def cubo_completo():
    """Ruta para c.iii: Muestra el cubo completo."""
    cubo = cubo_base(df)
    html_cubo = cubo.to_html(classes='tabla-olap', na_rep='-')
    return render_template(
        'cubo_completo.html',
        html_cubo=html_cubo,
        active_page='cubo_completo'
    )

@app.route('/cara')
def cara():
    """Ruta para c.i: Muestra una cara del cubo (Pivot)."""
    piv = pivot_anio_region(df)
    html_cara = piv.to_html(classes='tabla-olap', na_rep='-')
    return render_template(
        'cara.html',
        html_cara=html_cara,
        active_page='cara'
    )

@app.route('/seccion', methods=['GET', 'POST'])
def seccion():
    """Ruta para c.ii: Página interactiva para 'Sección' (Dice)."""
    
    # Valores por defecto para el primer render (GET)
    sel_seccion = {
        'anios': [2024, 2025],
        'regiones': ['Norte', 'Sur']
    }

    # Si se envía el formulario (POST)
    if request.method == 'POST':
        sel_seccion['anios'] = [int(a) for a in request.form.getlist('seccion_anios')]
        sel_seccion['regiones'] = request.form.getlist('seccion_regiones')

    # Esta lógica se ejecuta en GET (con valores por defecto) y en POST (con valores del form)
    df_seccion = dice_subset(
        df,
        anios=sel_seccion['anios'],
        regiones=sel_seccion['regiones']
    )
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

    return render_template(
        'seccion.html',
        html_seccion=html_seccion,
        opciones={'anios': TODOS_ANIOS, 'regiones': TODAS_REGIONES},
        sel_seccion=sel_seccion,
        active_page='seccion'
    )

@app.route('/drill', methods=['GET', 'POST'])
def drill():
    """Ruta para c.iv: Página interactiva para 'Drill-Through'."""
    
    # Valores por defecto
    sel_drill = {
        'anio': 2024,
        'trim': 1,
        'prod': 'A',
        'reg': 'Norte'
    }

    if request.method == 'POST':
        sel_drill['anio'] = int(request.form.get('drill_anio'))
        sel_drill['trim'] = int(request.form.get('drill_trim'))
        sel_drill['prod'] = request.form.get('drill_prod')
        sel_drill['reg'] = request.form.get('drill_reg')

    # Lógica del Drill-Through
    df_datos_celda = dice_subset(
        df,
        anios=[sel_drill['anio']],
        regiones=[sel_drill['reg']],
        productos=[sel_drill['prod']]
    )
    df_datos_celda = df_datos_celda[
        df_datos_celda["Trimestre"] == sel_drill['trim']
    ].copy()
    html_drill = df_datos_celda.to_html(classes='tabla-datos-crudos', index=False)
    
    return render_template(
        'drill.html',
        html_drill=html_drill,
        opciones={
            'anios': TODOS_ANIOS,
            'trimestres': TODOS_TRIMESTRES,
            'productos': TODOS_PRODUCTOS,
            'regiones': TODAS_REGIONES
        },
        sel_drill=sel_drill,
        active_page='drill'
    )

if __name__ == "__main__":
    app.run(debug=True)