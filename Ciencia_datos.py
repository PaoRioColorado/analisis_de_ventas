#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
                    PANEL DE VENTAS 2019 - VERSIÓN DEFINITIVA
================================================================================
Desarrollado por: Paola Dueña - Data Analyst
Versión: 5.0 - Entregable Final - Nombres Completos de Productos
================================================================================

Este dashboard interactivo proporciona un análisis completo de las ventas del año 2019,
permitiendo filtrar por múltiples dimensiones y visualizar los datos de manera dinámica.

CARACTERÍSTICAS PRINCIPALES:
    • 7 pestañas de análisis (General, Comparador, Producto, Horas, Eventos, Complementos, Propuestas)
    • Filtros globales por Estado, Ciudad, Mes, Día, Categoría, Rango de Precio y Fechas
    • Exportación a CSV, Excel y PDF con datos visibles
    • Análisis de producto estrella con insights automáticos
    • Mapas interactivos con nombres de estados visibles
    • Modales interactivos con detalles al hacer clic en gráficos
    • Propuestas estratégicas basadas en datos reales
    • Nombres completos de productos sin truncar

TECNOLOGÍAS UTILIZADAS:
    • Python 3.8+
    • Dash + Bootstrap para la interfaz web
    • Pandas + NumPy para procesamiento de datos
    • Plotly para visualizaciones interactivas
    • ReportLab para generación de PDF (opcional)
    • XlsxWriter para exportación Excel avanzada (opcional)
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output, callback, State, no_update
import dash_bootstrap_components as dbc
import glob
import os
import webbrowser
import threading
from datetime import datetime
from collections import Counter
from itertools import combinations
import sys
import warnings
import io
import base64
from dash.exceptions import PreventUpdate

# =============================================================================
# VERIFICACIÓN DE DEPENDENCIAS OPCIONALES
# =============================================================================
try:
    import xlsxwriter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️ xlsxwriter no instalado. La exportación a Excel usará formato básico.")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ reportlab no instalado. La exportación a PDF estará deshabilitada.")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    STATIC_PLOTS_AVAILABLE = True
except ImportError:
    STATIC_PLOTS_AVAILABLE = False
    print("⚠️ matplotlib/seaborn no instalados. Gráficos estáticos deshabilitados.")

# Suprimir warnings innecesarios
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURACIÓN GLOBAL
# =============================================================================
print("=" * 80)
print("PANEL DE VENTAS 2019 - VERSIÓN DEFINITIVA".center(80))
print("=" * 80)
print("Desarrollado por: Paola Dueña - Data Analyst".center(80))
print("Versión 5.0 - Entregable Final".center(80))
print("=" * 80)

# Constantes globales para mantener consistencia
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
MESES_DICT = {i + 1: mes for i, mes in enumerate(MESES)}

DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
COLORES = px.colors.qualitative.Set2

# =============================================================================
# 1. CARGA DE DATOS
# =============================================================================
print("\n📂 INICIALIZANDO DATA WAREHOUSE...")

# Configurar la ruta de los datos
ruta = r"C:\Users\USUARIO\Desktop\Ciencia de Datos\Dataset de ventas"
archivos = glob.glob(os.path.join(ruta, "Dataset_de_ventas_*.csv"))

# Verificar existencia de archivos
if not archivos:
    print("\n" + "=" * 80)
    print("❌ ERROR CRÍTICO".center(80))
    print("=" * 80)
    print("\nNo se encontraron archivos CSV en la ruta:")
    print(f"   {ruta}")
    print("\nPor favor, verifique la ruta e intente nuevamente.")
    sys.exit(1)

print(f"   ✅ Archivos encontrados: {len(archivos)}")
df_list = []

# Cargar cada archivo mensual
for archivo in archivos:
    nombre = os.path.basename(archivo)
    mes = nombre.replace('Dataset_de_ventas_', '').replace('.csv', '')
    print(f"      • Cargando: {nombre}")

    try:
        df_temp = pd.read_csv(archivo)
        df_temp = df_temp[df_temp['ID de Pedido'] != 'Order ID']
        df_temp = df_temp.dropna(subset=['ID de Pedido'])
        df_temp['Mes Archivo'] = mes
        df_list.append(df_temp)
    except Exception as e:
        print(f"      ⚠️ Error en {nombre}: {e}")
        continue

# Verificar que se cargaron datos
if not df_list:
    print("\n❌ No se pudo cargar ningún archivo válido")
    sys.exit(1)

# Combinar todos los meses
df = pd.concat(df_list, ignore_index=True)
print(f"\n   ✅ TOTAL: {len(df):,} registros procesados")

# =============================================================================
# 2. DATA WRANGLING Y LIMPIEZA
# =============================================================================
print("\n🔄 PROCESANDO DATOS...")

# Convertir a numérico y limpiar valores inválidos
df['Cantidad Pedida'] = pd.to_numeric(df['Cantidad Pedida'], errors='coerce')
df['Precio Unitario'] = pd.to_numeric(df['Precio Unitario'], errors='coerce')
df = df.dropna(subset=['Cantidad Pedida', 'Precio Unitario'])
df = df[(df['Cantidad Pedida'] > 0) & (df['Precio Unitario'] > 0)]

# Calcular ingreso total
df['Ingreso Total'] = df['Cantidad Pedida'] * df['Precio Unitario']

print("   • Procesando fechas...")
df['Fecha de Pedido'] = df['Fecha de Pedido'].astype(str)
df['Fecha Pedido'] = pd.to_datetime(df['Fecha de Pedido'], format='%m/%d/%y %H:%M', errors='coerce')
df = df.dropna(subset=['Fecha Pedido'])

# Extraer componentes de fecha
df['Fecha'] = df['Fecha Pedido'].dt.date
df['Mes Num'] = df['Fecha Pedido'].dt.month
df['Día'] = df['Fecha Pedido'].dt.day
df['Hora'] = df['Fecha Pedido'].dt.hour
df['Día Semana'] = df['Fecha Pedido'].dt.dayofweek
df['Semana'] = df['Fecha Pedido'].dt.isocalendar().week
df['Día del Año'] = df['Fecha Pedido'].dt.dayofyear
df['Es Finde'] = df['Día Semana'].isin([5, 6])
df['Mes'] = df['Mes Num'].map(MESES_DICT)

# Mapear días a español
dias_ingles_a_espanol = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}
df['Día Semana Nombre'] = df['Fecha Pedido'].dt.day_name().map(dias_ingles_a_espanol)

# =============================================================================
# 3. EXTRACCIÓN DE UBICACIÓN
# =============================================================================
print("   • Procesando ubicaciones...")

def extraer_ubicacion(direccion):
    """
    Extrae ciudad y estado de una dirección completa.
    """
    try:
        if pd.isna(direccion):
            return pd.Series(['Desconocido', 'Desconocido'])

        partes = str(direccion).split(',')
        if len(partes) >= 3:
            ciudad = partes[1].strip()
            estado_zip = partes[2].strip().split()
            estado = estado_zip[0] if estado_zip else 'Desconocido'
            return pd.Series([ciudad, estado])
    except:
        pass
    return pd.Series(['Desconocido', 'Desconocido'])

df[['Ciudad', 'Estado']] = df['Dirección de Envio'].apply(extraer_ubicacion)

# =============================================================================
# 4. CATEGORIZACIÓN DE PRODUCTOS
# =============================================================================
print("   • Clasificando productos en categorías...")

def asignar_categoria(producto):
    """
    Asigna una categoría basada en palabras clave en el nombre del producto.
    """
    producto = str(producto).lower()

    categorias = {
        'Baterías': ['batteries', 'battery'],
        'Cables': ['cable'],
        'Auriculares': ['headphones', 'airpods', 'earpods', 'bose'],
        'Monitores': ['monitor', 'screen'],
        'Computadoras': ['laptop', 'macbook', 'thinkpad'],
        'Teléfonos': ['phone', 'iphone'],
        'Televisores': ['tv'],
        'Electrodomésticos': ['washing machine', 'dryer', 'lg']
    }

    for categoria, keywords in categorias.items():
        if any(keyword in producto for keyword in keywords):
            return categoria
    return 'Otros'

df['Categoría'] = df['Producto'].apply(asignar_categoria)

# Rangos de precio
bins = [0, 20, 50, 100, 500, 1000, 10000]
labels = ['Económico', 'Bajo', 'Medio', 'Premium', 'Alta Gama', 'Lujo']
df['Rango Precio'] = pd.cut(df['Precio Unitario'], bins=bins, labels=labels)

print(f"      • Categorías encontradas: {df['Categoría'].nunique()}")
print(f"      • Rangos de precio: {df['Rango Precio'].nunique()}")

# =============================================================================
# 5. MAPA DE ESTADOS (USA)
# =============================================================================
print("   • Mapeando estados...")

# Diccionario de códigos a nombres completos
estados_usa = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'Nueva York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
}

# Invertir para obtener nombre a código
nombre_a_codigo = {v: k for k, v in estados_usa.items()}
nombre_a_codigo['Desconocido'] = 'NA'

df['Estado Nombre'] = df['Estado'].map(estados_usa).fillna(df['Estado'])
df['Estado Codigo'] = df['Estado Nombre'].map(nombre_a_codigo).fillna('NA')

# =============================================================================
# 6. EVENTOS ESPECIALES
# =============================================================================
print("\n🎉 Configurando eventos especiales...")

eventos = {
    'Año Nuevo': ['2019-01-01'],
    'San Valentín': ['2019-02-14'],
    'Día de San Patricio': ['2019-03-17'],
    'Pascua': ['2019-04-21'],
    'Día de la Madre': ['2019-05-12'],
    'Día del Padre': ['2019-06-16'],
    'Independencia': ['2019-07-04'],
    'Back to School': [f'2019-08-{d}' for d in range(15, 20)],
    'Labor Day': ['2019-09-02'],
    'Halloween': ['2019-10-31'],
    'Veterans Day': ['2019-11-11'],
    'Black Friday': ['2019-11-29'],
    'Cyber Monday': ['2019-12-02'],
    'Navidad': ['2019-12-24', '2019-12-25']
}

def identificar_evento(fecha):
    """
    Identifica si una fecha corresponde a un evento especial.
    """
    fecha_str = fecha.strftime('%Y-%m-%d')
    for evento, fechas in eventos.items():
        if fecha_str in fechas:
            return evento
    return 'Normal'

print("   • Identificando eventos en los datos...")
df['Evento'] = df['Fecha Pedido'].apply(identificar_evento)

eventos_con_datos = []
for evento in eventos.keys():
    count = len(df[df['Evento'] == evento])
    if count > 0:
        eventos_con_datos.append(evento)
        print(f"      ✅ {evento}: {count:,.0f} registros")

print(f"   • Total eventos con datos: {len(eventos_con_datos)}")

# =============================================================================
# 7. ESTADÍSTICAS CON NUMPY
# =============================================================================
print("\n🔢 ESTADÍSTICAS CON NUMPY:")

precios = df['Precio Unitario'].values
cantidades = df['Cantidad Pedida'].values
ingresos = df['Ingreso Total'].values

media_precio = np.mean(precios)
mediana_precio = np.median(precios)
std_precio = np.std(precios)
min_precio = np.min(precios)
max_precio = np.max(precios)
percentil_90 = np.percentile(precios, 90)

print(f"   • Media de precios: ${media_precio:.2f}")
print(f"   • Mediana de precios: ${mediana_precio:.2f}")
print(f"   • Desviación estándar: ${std_precio:.2f}")
print(f"   • Rango de precios: ${min_precio:.2f} - ${max_precio:.2f}")
print(f"   • Percentil 90: ${percentil_90:.2f}")

correlacion = np.corrcoef(cantidades, precios)[0, 1]
print(f"   • Correlación cantidad-precio: {correlacion:.3f}")

total_ingresos_np = np.sum(ingresos)
print(f"   • Total ingresos (np.sum): ${total_ingresos_np:,.0f}")

# =============================================================================
# 8. GRÁFICOS ESTÁTICOS (OPCIONAL)
# =============================================================================
if STATIC_PLOTS_AVAILABLE:
    print("\n📊 Generando visualizaciones adicionales...")

    def generar_graficos_estaticos(data):
        """
        Genera gráficos estáticos con Matplotlib/Seaborn.
        """
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

        fig = plt.figure(figsize=(20, 12))
        fig.suptitle('ANÁLISIS DE VENTAS 2019 - GRÁFICOS ESTÁTICOS',
                     fontsize=16, fontweight='bold', y=0.98)

        # 1. Ventas por mes
        ax1 = plt.subplot(2, 3, 1)
        ventas_mes = data.groupby('Mes Num')['Ingreso Total'].sum().reset_index()
        meses_abrev = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        ax1.bar(meses_abrev, ventas_mes['Ingreso Total'],
                color='#3498db', edgecolor='#2c3e50')
        ax1.set_title('💰 Ventas por Mes', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Mes')
        ax1.set_ylabel('Ingresos ($)')
        ax1.tick_params(axis='x', rotation=45)

        # 2. Distribución por hora
        ax2 = plt.subplot(2, 3, 2)
        ventas_hora = data.groupby('Hora')['ID de Pedido'].nunique().reset_index()
        ax2.plot(ventas_hora['Hora'], ventas_hora['ID de Pedido'],
                 marker='o', linewidth=2, color='#e74c3c')
        ax2.fill_between(ventas_hora['Hora'], ventas_hora['ID de Pedido'], alpha=0.3, color='#e74c3c')
        ax2.set_title('⏰ Pedidos por Hora', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Hora del Día')
        ax2.set_ylabel('Cantidad de Pedidos')
        ax2.grid(True, alpha=0.3)

        # 3. Top 10 ciudades
        ax3 = plt.subplot(2, 3, 3)
        top_ciudades = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
        sns.barplot(data=top_ciudades, y='Ciudad', x='Ingreso Total',
                    palette='Reds_r', ax=ax3)
        ax3.set_title('🏙️ Top 10 Ciudades', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Ingresos ($)')

        # 4. Mapa de calor Día vs Hora
        ax4 = plt.subplot(2, 3, 4)
        pivot = data.pivot_table(
            index='Día Semana Nombre',
            columns='Hora',
            values='ID de Pedido',
            aggfunc='count',
            fill_value=0
        )
        pivot = pivot.reindex(DIAS)
        sns.heatmap(pivot, cmap='YlOrRd', ax=ax4,
                    cbar_kws={'label': 'Cantidad de Pedidos'})
        ax4.set_title('🔥 Mapa de Calor: Día vs Hora', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Hora del Día')

        # 5. Distribución de precios
        ax5 = plt.subplot(2, 3, 5)
        sns.histplot(data=data, x='Precio Unitario', bins=50,
                     kde=True, color='#2ecc71', ax=ax5)
        ax5.set_title('📦 Distribución de Precios', fontsize=12, fontweight='bold')
        ax5.set_xlabel('Precio Unitario ($)')
        ax5.axvline(media_precio, color='red', linestyle='--', label=f'Media: ${media_precio:.2f}')
        ax5.axvline(mediana_precio, color='blue', linestyle='--', label=f'Mediana: ${mediana_precio:.2f}')
        ax5.legend()

        # 6. Ventas por categoría
        ax6 = plt.subplot(2, 3, 6)
        ventas_cat = data.groupby('Categoría')['Ingreso Total'].sum().sort_values(ascending=False).head(8)
        ax6.barh(ventas_cat.index, ventas_cat.values, color='#9b59b6')
        ax6.set_title('📊 Ventas por Categoría', fontsize=12, fontweight='bold')
        ax6.set_xlabel('Ingresos ($)')

        plt.tight_layout()
        filename = f'graficos_estaticos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

        return filename

    graficos_filename = generar_graficos_estaticos(df)
    print(f"   ✅ Visualizaciones guardadas como: {graficos_filename}")

# =============================================================================
# 9. ANÁLISIS DE INGRESOS POR HORA
# =============================================================================
print("\n💰 ANÁLISIS DE INGRESOS POR HORA:")

ingresos_hora = df.groupby('Hora')['Ingreso Total'].agg(['sum', 'mean', 'count']).reset_index()
ingresos_hora.columns = ['Hora', 'Ingresos Totales', 'Ticket Promedio', 'Cantidad Pedidos']

print("\n   Top 5 horas por ingresos:")
for _, row in ingresos_hora.nlargest(5, 'Ingresos Totales').iterrows():
    print(f"      • {int(row['Hora']):02d}:00 - ${row['Ingresos Totales']:,.0f} ({row['Cantidad Pedidos']:.0f} pedidos)")

print("\n   Top 5 horas por ticket promedio:")
for _, row in ingresos_hora.nlargest(5, 'Ticket Promedio').iterrows():
    print(f"      • {int(row['Hora']):02d}:00 - ${row['Ticket Promedio']:.2f}")

# =============================================================================
# 10. KPIs GLOBALES
# =============================================================================
print("\n📊 CALCULANDO KPIs GLOBALES...")

TOTAL_INGRESOS = np.sum(ingresos)
TOTAL_PEDIDOS = df['ID de Pedido'].nunique()
TOTAL_UNIDADES = np.sum(cantidades)
TICKET_PROMEDIO = TOTAL_INGRESOS / TOTAL_PEDIDOS if TOTAL_PEDIDOS > 0 else 0
PRODUCTO_TOP = df.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
CIUDAD_TOP = df.groupby('Ciudad')['Ingreso Total'].sum().idxmax()
ESTADO_TOP = df.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax()
CATEGORIA_TOP = df.groupby('Categoría')['Ingreso Total'].sum().idxmax()

hora_pedidos = df.groupby('Hora')['ID de Pedido'].nunique().idxmax()
hora_ingresos = df.groupby('Hora')['Ingreso Total'].sum().idxmax()

if hora_pedidos == hora_ingresos:
    HORA_OPTIMA = hora_pedidos
    RAZON_HORA = "máximo en pedidos e ingresos"
else:
    ingresos_hora_pedidos = df[df['Hora'] == hora_pedidos]['Ingreso Total'].sum()
    ingresos_hora_ingresos = df[df['Hora'] == hora_ingresos]['Ingreso Total'].sum()
    HORA_OPTIMA = hora_ingresos if ingresos_hora_ingresos > ingresos_hora_pedidos * 1.2 else hora_pedidos
    RAZON_HORA = "mayor facturación" if HORA_OPTIMA == hora_ingresos else "mayor volumen"

DIA_PICO = df.groupby('Día Semana Nombre')['ID de Pedido'].nunique().idxmax()

ventas_mensuales = df.groupby('Mes Num')['Ingreso Total'].sum()
if len(ventas_mensuales) > 1:
    CRECIMIENTO_ANUAL = ((ventas_mensuales.iloc[-1] / ventas_mensuales.iloc[0] - 1) * 100)
else:
    CRECIMIENTO_ANUAL = 0

print(f"\n📊 RESUMEN DE DATOS:")
print(f"   • {len(df):,} registros válidos")
print(f"   • {df['Ciudad'].nunique()} ciudades | {df['Estado Nombre'].nunique()} estados")
print(f"   • {df['Categoría'].nunique()} categorías de productos")
print(f"   • Período: {df['Fecha'].min()} a {df['Fecha'].max()}")
print(f"   • Ingresos totales: ${TOTAL_INGRESOS:,.0f}")
print(f"   • Crecimiento: {CRECIMIENTO_ANUAL:+.1f}%")
print(f"   • ⏰ Hora óptima: {HORA_OPTIMA}:00 ({RAZON_HORA})")
print(f"   • 📆 Mejor día: {DIA_PICO}")
print(f"   • 🏆 Producto estrella: {PRODUCTO_TOP}")
print(f"   • 📦 Categoría top: {CATEGORIA_TOP}")

# =============================================================================
# 11. FUNCIÓN PRODUCTO ESTRELLA
# =============================================================================
def analizar_producto_estrella(data, filtro_temporal):
    """
    Analiza el producto estrella generando insights detallados.

    Parámetros:
        data (DataFrame): Datos filtrados
        filtro_temporal (str): Descripción del filtro aplicado

    Retorna:
        dict: Diccionario con análisis detallado o None si no hay datos
    """
    if data.empty or len(data) < 10:
        return None

    try:
        ventas_productos = data.groupby('Producto').agg({
            'Cantidad Pedida': 'sum',
            'Ingreso Total': 'sum',
            'ID de Pedido': 'nunique',
            'Precio Unitario': 'mean'
        }).reset_index()

        ventas_productos = ventas_productos.sort_values('Cantidad Pedida', ascending=False)

        if ventas_productos.empty:
            return None

        producto_top = ventas_productos.iloc[0]
        total_unidades = ventas_productos['Cantidad Pedida'].sum()
        share_producto = (producto_top['Cantidad Pedida'] / total_unidades * 100) if total_unidades > 0 else 0
        precio_promedio = data['Precio Unitario'].mean()
        comparacion_precio = ((producto_top['Precio Unitario'] - precio_promedio) / precio_promedio * 100) if precio_promedio > 0 else 0

        datos_producto = data[data['Producto'] == producto_top['Producto']]
        ventas_por_mes_prod = datos_producto.groupby('Mes')['Cantidad Pedida'].sum()
        mes_pico = ventas_por_mes_prod.idxmax() if not ventas_por_mes_prod.empty else "N/A"
        ciudades_top_prod = datos_producto.groupby('Ciudad')['Cantidad Pedida'].sum().nlargest(3).index.tolist()

        # Generar insights automáticos
        insights = []
        if share_producto > 20:
            insights.append(f"🔥 DOMINANTE: {share_producto:.1f}% del total de unidades vendidas")
        elif share_producto > 10:
            insights.append(f"📊 SIGNIFICATIVO: {share_producto:.1f}% del total de unidades vendidas")
        else:
            insights.append(f"📈 NICHO: {share_producto:.1f}% del total de unidades vendidas")

        if comparacion_precio > 20:
            insights.append(f"💎 PREMIUM: ${producto_top['Precio Unitario']:.2f} ({comparacion_precio:+.1f}% vs precio promedio)")
        elif comparacion_precio < -20:
            insights.append(f"💰 ECONÓMICO: ${producto_top['Precio Unitario']:.2f} ({comparacion_precio:+.1f}% vs precio promedio)")
        else:
            insights.append(f"⚖️ COMPETITIVO: ${producto_top['Precio Unitario']:.2f}")

        if producto_top['Cantidad Pedida'] > 1000:
            insights.append(f"📦 ALTO VOLUMEN: {producto_top['Cantidad Pedida']:,.0f} unidades")
        elif producto_top['Cantidad Pedida'] > 500:
            insights.append(f"📦 VOLUMEN MEDIO: {producto_top['Cantidad Pedida']:,.0f} unidades")
        else:
            insights.append(f"📦 BAJO VOLUMEN: {producto_top['Cantidad Pedida']:,.0f} unidades")

        factores_exito = [
            f"📅 Pico de ventas: {mes_pico}",
            f"📍 Principales ciudades: {', '.join(ciudades_top_prod[:2])}",
            f"💵 Precio {('competitivo' if -20 < comparacion_precio < 20 else 'premium' if comparacion_precio > 20 else 'económico')}"
        ]

        return {
            'producto': producto_top['Producto'],
            'unidades': producto_top['Cantidad Pedida'],
            'ingresos': producto_top['Ingreso Total'],
            'pedidos': producto_top['ID de Pedido'],
            'precio': producto_top['Precio Unitario'],
            'share': share_producto,
            'comparacion_precio': comparacion_precio,
            'insights': insights,
            'factores_exito': factores_exito,
            'mes_pico': mes_pico,
            'ciudades_top': ciudades_top_prod,
            'filtro_aplicado': filtro_temporal
        }
    except Exception as e:
        print(f"   ⚠️ Error en análisis de producto: {e}")
        return None

# =============================================================================
# 12. FUNCIÓN PRODUCTOS COMPLEMENTARIOS
# =============================================================================
def analizar_productos_complementarios(data):
    """
    Analiza qué productos se compran juntos con mayor frecuencia.

    Parámetros:
        data (DataFrame): Datos filtrados

    Retorna:
        list: Lista de tuplas (producto A, producto B, frecuencia)
    """
    if data.empty or len(data) < 100:
        return []

    try:
        pedidos = data.groupby('ID de Pedido')['Producto'].agg(list)
        pares = Counter()

        for productos in pedidos[pedidos.apply(len) > 1]:
            pares.update(combinations(sorted(set(productos)), 2))

        return pares.most_common(5)
    except:
        return []

# =============================================================================
# 13. FUNCIÓN AUXILIAR DE FILTRADO
# =============================================================================
def obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end):
    """
    Aplica todos los filtros seleccionados a los datos.

    Parámetros:
        ciudad (str): Ciudad seleccionada
        estado (str): Estado seleccionado
        mes (str): Mes seleccionado
        dia (str): Día seleccionado
        categoria (str): Categoría seleccionada
        rango (str): Rango de precio seleccionado
        start (str): Fecha de inicio
        end (str): Fecha de fin

    Retorna:
        DataFrame: Datos filtrados
    """
    data = df.copy()

    if estado != 'Todos':
        data = data[data['Estado Nombre'] == estado]
    if ciudad != 'Todas':
        data = data[data['Ciudad'] == ciudad]
    if mes != 'Todos':
        data = data[data['Mes'] == mes]
    if dia != 'Todos':
        data = data[data['Día Semana Nombre'] == dia]
    if categoria != 'Todas':
        data = data[data['Categoría'] == categoria]
    if rango != 'Todos':
        data = data[data['Rango Precio'] == rango]

    try:
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        data = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    except:
        pass

    return data

# =============================================================================
# 14. FUNCIONES DE EXPORTACIÓN
# =============================================================================

def generar_excel_datos_visibles(data):
    """
    Genera un archivo Excel con los datos agregados visibles en pantalla.
    """
    try:
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter' if EXCEL_AVAILABLE else 'openpyxl') as writer:
            # Resumen ejecutivo
            resumen = pd.DataFrame({
                'Métrica': ['Total Ingresos', 'Total Pedidos', 'Total Unidades', 'Ticket Promedio',
                           'Período', 'Ciudades', 'Estados', 'Categorías'],
                'Valor': [
                    f"${data['Ingreso Total'].sum():,.0f}",
                    f"{data['ID de Pedido'].nunique():,}",
                    f"{data['Cantidad Pedida'].sum():,}",
                    f"${data['Ingreso Total'].sum() / data['ID de Pedido'].nunique():,.2f}",
                    f"{data['Fecha'].min()} a {data['Fecha'].max()}",
                    f"{data['Ciudad'].nunique():,}",
                    f"{data['Estado Nombre'].nunique():,}",
                    f"{data['Categoría'].nunique():,}"
                ]
            })
            resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)

            # Ventas por mes
            ventas_mes = data.groupby('Mes').agg({
                'Ingreso Total': 'sum',
                'ID de Pedido': 'nunique',
                'Cantidad Pedida': 'sum'
            }).reset_index()
            ventas_mes['Mes'] = pd.Categorical(ventas_mes['Mes'], categories=MESES, ordered=True)
            ventas_mes = ventas_mes.sort_values('Mes')
            ventas_mes.to_excel(writer, sheet_name='Ventas por Mes', index=False)

            # Top 10 ciudades
            ventas_ciudad = data.groupby('Ciudad').agg({
                'Ingreso Total': 'sum',
                'ID de Pedido': 'nunique'
            }).reset_index().sort_values('Ingreso Total', ascending=False).head(10)
            ventas_ciudad.to_excel(writer, sheet_name='Top 10 Ciudades', index=False)

            # Ventas por estado
            ventas_estado = data.groupby('Estado Nombre').agg({
                'Ingreso Total': 'sum',
                'ID de Pedido': 'nunique'
            }).reset_index().sort_values('Ingreso Total', ascending=False)
            ventas_estado.to_excel(writer, sheet_name='Ventas por Estado', index=False)

            # Ventas por hora
            ventas_hora = data.groupby('Hora').agg({
                'ID de Pedido': 'nunique',
                'Ingreso Total': 'sum'
            }).reset_index().sort_values('Hora')
            ventas_hora.to_excel(writer, sheet_name='Ventas por Hora', index=False)

            # Ventas por día
            ventas_dia = data.groupby('Día Semana Nombre').agg({
                'ID de Pedido': 'nunique',
                'Ingreso Total': 'sum'
            }).reset_index()
            ventas_dia['Día Semana Nombre'] = pd.Categorical(ventas_dia['Día Semana Nombre'], categories=DIAS, ordered=True)
            ventas_dia = ventas_dia.sort_values('Día Semana Nombre')
            ventas_dia.to_excel(writer, sheet_name='Ventas por Día', index=False)

            # Top 20 productos
            top_productos = data.groupby('Producto').agg({
                'Cantidad Pedida': 'sum',
                'Ingreso Total': 'sum',
                'Precio Unitario': 'mean'
            }).reset_index().sort_values('Cantidad Pedida', ascending=False).head(20)
            top_productos.to_excel(writer, sheet_name='Top 20 Productos', index=False)

            # Producto estrella por mes
            prods_mes = data.groupby(['Mes', 'Producto'])['Cantidad Pedida'].sum().reset_index()
            idx = prods_mes.groupby('Mes')['Cantidad Pedida'].idxmax()
            top_mes = prods_mes.loc[idx].reset_index(drop=True)
            top_mes['Mes'] = pd.Categorical(top_mes['Mes'], categories=MESES, ordered=True)
            top_mes = top_mes.sort_values('Mes')
            top_mes.to_excel(writer, sheet_name='Producto Estrella por Mes', index=False)

            # Ventas por categoría
            ventas_categoria = data.groupby('Categoría').agg({
                'Ingreso Total': 'sum',
                'ID de Pedido': 'nunique',
                'Cantidad Pedida': 'sum'
            }).reset_index().sort_values('Ingreso Total', ascending=False)
            ventas_categoria.to_excel(writer, sheet_name='Ventas por Categoría', index=False)

            # Productos complementarios
            top_pares = analizar_productos_complementarios(data)
            if top_pares:
                pares_data = []
                for (a, b), c in top_pares:
                    pares_data.append({'Producto A': a, 'Producto B': b, 'Frecuencia': c})
                pares_df = pd.DataFrame(pares_data)
                pares_df.to_excel(writer, sheet_name='Productos Complementarios', index=False)

        return base64.b64encode(output.getvalue()).decode('utf-8')

    except Exception as e:
        print(f"Error generando Excel: {e}")
        return None

def generar_csv_datos_visibles(data):
    """
    Genera un archivo CSV con los datos agregados visibles en pantalla.
    """
    output = io.StringIO()

    output.write("=== RESUMEN EJECUTIVO ===\n")
    output.write(f"Total Ingresos,${data['Ingreso Total'].sum():,.0f}\n")
    output.write(f"Total Pedidos,{data['ID de Pedido'].nunique():,}\n")
    output.write(f"Total Unidades,{data['Cantidad Pedida'].sum():,}\n")
    output.write(f"Ticket Promedio,${data['Ingreso Total'].sum() / data['ID de Pedido'].nunique():,.2f}\n")
    output.write(f"Período,{data['Fecha'].min()} a {data['Fecha'].max()}\n")
    output.write(f"Ciudades,{data['Ciudad'].nunique()}\n")
    output.write(f"Estados,{data['Estado Nombre'].nunique()}\n")
    output.write(f"Categorías,{data['Categoría'].nunique()}\n\n")

    output.write("=== VENTAS POR MES ===\n")
    ventas_mes = data.groupby('Mes')['Ingreso Total'].sum()
    for mes in MESES:
        valor = ventas_mes.get(mes, 0)
        output.write(f"{mes},${valor:,.0f}\n")
    output.write("\n")

    output.write("=== TOP 10 CIUDADES ===\n")
    top_ciudades = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10)
    for ciudad, valor in top_ciudades.items():
        output.write(f"{ciudad},${valor:,.0f}\n")
    output.write("\n")

    output.write("=== VENTAS POR CATEGORÍA ===\n")
    ventas_cat = data.groupby('Categoría')['Ingreso Total'].sum().sort_values(ascending=False)
    for cat, valor in ventas_cat.items():
        output.write(f"{cat},${valor:,.0f}\n")
    output.write("\n")

    output.write("=== VENTAS POR HORA ===\n")
    ventas_hora = data.groupby('Hora')['ID de Pedido'].nunique()
    for hora in range(24):
        pedidos = ventas_hora.get(hora, 0)
        output.write(f"{hora:02d}:00,{pedidos} pedidos\n")

    return output.getvalue()

def generar_informe_pdf_datos_visibles(data, titulo):
    """
    Genera un informe PDF con los datos agregados visibles en pantalla.
    """
    if not PDF_AVAILABLE:
        return None

    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph(titulo, title_style))
        story.append(Spacer(1, 12))

        fecha_style = ParagraphStyle(
            'Fecha',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray
        )
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))
        story.append(Spacer(1, 20))

        # KPIs principales
        kpi_data = [
            ['Métrica', 'Valor'],
            ['Ingresos Totales', f'${data["Ingreso Total"].sum():,.0f}'],
            ['Total Pedidos', f'{data["ID de Pedido"].nunique():,}'],
            ['Unidades Vendidas', f'{data["Cantidad Pedida"].sum():,}'],
            ['Ticket Promedio', f'${data["Ingreso Total"].sum() / data["ID de Pedido"].nunique():,.2f}'],
            ['Producto más vendido', data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()[:40]],
            ['Categoría top', data.groupby('Categoría')['Ingreso Total'].sum().idxmax()],
            ['Hora pico', f"{data.groupby('Hora')['ID de Pedido'].nunique().idxmax()}:00"],
            ['Mejor día', data.groupby('Día Semana Nombre')['ID de Pedido'].nunique().idxmax()]
        ]

        kpi_table = Table(kpi_data, colWidths=[2.5 * inch, 3.5 * inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 20))

        # Top 5 productos
        story.append(Paragraph("Top 5 Productos Más Vendidos", styles['Heading2']))
        story.append(Spacer(1, 12))

        top_prod = data.groupby('Producto')['Cantidad Pedida'].sum().nlargest(5).reset_index()
        top_prod.columns = ['Producto', 'Unidades']

        prod_data = [['Producto', 'Unidades Vendidas']]
        for _, row in top_prod.iterrows():
            prod_data.append([row['Producto'][:40], f"{row['Unidades']:,}"])

        prod_table = Table(prod_data, colWidths=[4 * inch, 1.5 * inch])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(prod_table)

        doc.build(story)

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        os.unlink(pdf_path)
        return base64.b64encode(pdf_bytes).decode('utf-8')

    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None

# =============================================================================
# 15. CONFIGURACIÓN DEL DASHBOARD
# =============================================================================
print("\n🚀 Inicializando dashboard...")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Panel de Ventas 2019 - Análisis Completo"

# Listas para dropdowns
estados_list = ['Todos'] + sorted(df['Estado Nombre'].unique())
ciudades_list = ['Todas'] + sorted(df['Ciudad'].unique())
meses_list = ['Todos'] + MESES
dias_list = ['Todos'] + DIAS
categorias_list = ['Todas'] + sorted(df['Categoría'].unique())
rangos_list = ['Todos'] + sorted(df['Rango Precio'].dropna().unique())

filtros_temporales = [
    {'label': '🌐 General', 'value': 'General'},
    {'label': '📅 Por Mes', 'value': 'Mes'},
    {'label': '📆 Por Semana', 'value': 'Semana'},
    {'label': '📊 Por Día', 'value': 'Día'}
]

# =============================================================================
# 16. LAYOUT PRINCIPAL
# =============================================================================
app.layout = dbc.Container([

    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("📊 PANEL DE VENTAS 2019", className="text-center text-white fw-bold"),
                html.H5("Análisis Completo de Ventas", className="text-center text-white-50"),
                html.Hr(className="bg-white opacity-25"),
                html.P(id='subtitulo', className="text-center text-white small mb-0"),
            ], className="p-4 bg-primary rounded-3")
        ], width=12)
    ], className="mb-4"),

    # Filtros globales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 FILTROS GLOBALES", className="bg-dark text-white fw-bold"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📍 Estado", className="fw-bold"),
                            dcc.Dropdown(
                                id='estado',
                                options=[{'label': e, 'value': e} for e in estados_list],
                                value='Todos',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("🏙️ Ciudad", className="fw-bold"),
                            dcc.Dropdown(id='ciudad', options=[{'label': 'Todas', 'value': 'Todas'}], value='Todas', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("📅 Mes", className="fw-bold"),
                            dcc.Dropdown(id='mes', options=[{'label': m, 'value': m} for m in meses_list], value='Todos', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("📆 Día", className="fw-bold"),
                            dcc.Dropdown(id='dia', options=[{'label': d, 'value': d} for d in dias_list], value='Todos', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("📦 Categoría", className="fw-bold"),
                            dcc.Dropdown(id='categoria', options=[{'label': c, 'value': c} for c in categorias_list], value='Todas', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("💰 Rango", className="fw-bold"),
                            dcc.Dropdown(id='rango', options=[{'label': r, 'value': r} for r in rangos_list], value='Todos', clearable=False)
                        ], width=2),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Label("📅 Rango de Fechas", className="fw-bold mt-3"),
                            dcc.DatePickerRange(
                                id='fechas',
                                start_date=df['Fecha'].min(),
                                end_date=df['Fecha'].max(),
                                display_format='DD/MM/YYYY',
                                className="form-control w-100"
                            )
                        ], width=10),
                        dbc.Col([
                            html.Label("🔄", className="fw-bold mt-3"),
                            html.Button("🔄 RESETEAR FILTROS", id='reset', className="btn btn-outline-danger w-100")
                        ], width=2),
                    ]),
                ])
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),

    # Barra de exportación
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("📥 EXPORTAR ANÁLISIS", className="d-inline"),
                            html.Span(" (Datos visibles en pantalla)", className="text-muted small ms-2"),
                        ], width=4),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("📊 CSV", id="btn-csv", color="success", className="me-1", size="sm"),
                                dbc.Button("📗 Excel", id="btn-excel", color="primary", className="me-1", size="sm"),
                                dbc.Button("📘 PDF", id="btn-pdf", color="danger", className="me-1", size="sm", disabled=not PDF_AVAILABLE),
                                dbc.Button("📑 Informe Completo", id="btn-informe", color="info", size="sm", disabled=not PDF_AVAILABLE),
                            ]),
                        ], width=8),
                    ]),
                ])
            ], className="shadow-sm bg-light")
        ], width=12)
    ], className="mb-4"),

    # Tabs principales
    dbc.Tabs([

        # TAB 1: GENERAL
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 KPIs PRINCIPALES", className="bg-primary text-white fw-bold"),
                        dbc.CardBody(id='kpis')
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 ANÁLISIS DE TENDENCIAS", className="bg-info text-white"),
                        dbc.CardBody(id='tendencias')
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("💰 Ventas por Mes"), dbc.CardBody(dcc.Graph(id='graf-mes'))]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("📈 Tendencia Diaria"), dbc.CardBody(dcc.Graph(id='graf-tendencia'))]), width=6)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🏙️ Top 10 Ciudades"), dbc.CardBody(dcc.Graph(id='graf-ciudades'))]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("🗺️ Mapa de Estados"), dbc.CardBody(dcc.Graph(id='mapa-estados'))]), width=6)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("📊 Ventas por Estado"), dbc.CardBody(dcc.Graph(id='graf-estados-barras'))]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("📦 Ventas por Categoría"), dbc.CardBody(dcc.Graph(id='graf-categorias'))]), width=6)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader(id='titulo-variacion'),
                    dbc.CardBody(dcc.Graph(id='graf-estados-mensual'))
                ], className="shadow-sm"), width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🎯 RESUMEN EJECUTIVO", className="bg-warning text-dark"), dbc.CardBody(id='resumen')]), width=12)
            ]),

            dcc.Download(id="download-csv"),
            dcc.Download(id="download-excel"),
            dcc.Download(id="download-pdf"),
            dcc.Download(id="download-informe"),

        ], label="📊 GENERAL"),

        # TAB 2: COMPARADOR
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📅 COMPARADOR DE MESES", className="bg-danger text-white fw-bold"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Selecciona hasta 3 meses para comparar:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='comp-meses',
                                        options=[{'label': m, 'value': m} for m in MESES],
                                        value=['Enero', 'Febrero', 'Marzo'],
                                        multi=True,
                                        placeholder="Selecciona meses..."
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Métrica a comparar:", className="fw-bold"),
                                    dcc.RadioItems(
                                        id='comp-metrica',
                                        options=[
                                            {'label': '💰 Ingresos', 'value': 'ingresos'},
                                            {'label': '📦 Pedidos', 'value': 'pedidos'}
                                        ],
                                        value='ingresos',
                                        inline=True
                                    )
                                ], width=6),
                            ]),
                            html.Div(id='comp-kpis', className="mt-3")
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("📈 Tendencia Comparativa"), dbc.CardBody(dcc.Graph(id='graf-comp-tend'))]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("📊 Distribución por Hora"), dbc.CardBody(dcc.Graph(id='graf-comp-dist'))]), width=6)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("📋 Tabla Comparativa Detallada"), dbc.CardBody(id='comp-tabla')]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("🏆 Producto por Mes"), dbc.CardBody(id='comp-productos')]), width=6)
            ]),

        ], label="📅 COMPARADOR"),

        # TAB 3: PRODUCTO ESTRELLA
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏆 PRODUCTO ESTRELLA", className="bg-warning text-dark fw-bold"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("🔍 Analizar por:", className="fw-bold"),
                                    dcc.RadioItems(
                                        id='filtro-prod',
                                        options=filtros_temporales,
                                        value='General',
                                        inline=True
                                    )
                                ], width=8),
                                dbc.Col(html.Div(id='indicador-prod', className="mt-2 text-end text-primary fw-bold"), width=4),
                            ]),
                            html.Hr(),
                            html.Div(id='prod-container'),
                            html.Hr(),
                            html.Div(id='factores-prod')
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("📋 Producto por Mes"), dbc.CardBody(id='tabla-prod-mes')]), width=12)
            ]),

        ], label="🏆 PRODUCTO"),

        # TAB 4: ANÁLISIS DE HORAS
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("⏰ ANÁLISIS DE HORAS", className="bg-secondary text-white fw-bold"),
                        dbc.CardBody([
                            dcc.Tabs([
                                dcc.Tab(label="📊 Frecuencia de Pedidos", children=[
                                    dcc.Graph(id='graf-horas-dist'),
                                    html.P("👆 Haz clic en cualquier barra para ver los productos más vendidos en esa hora",
                                           className="text-info text-center small mt-2")
                                ]),
                                dcc.Tab(label="💰 Ingresos por Hora", children=[
                                    dcc.Graph(id='graf-ingresos-hora'),
                                    html.P("👆 Haz clic en cualquier barra para ver detalles de ingresos",
                                           className="text-info text-center small mt-2")
                                ]),
                                dcc.Tab(label="🔥 Heatmap Hora vs Mes", children=[dcc.Graph(id='graf-horas-heat')]),
                            ])
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🔥 Mapa de Calor Día vs Hora"), dbc.CardBody(dcc.Graph(id='graf-heatmap'))]), width=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("📆 Ventas por Día"),
                    dbc.CardBody([
                        dcc.Graph(id='graf-dias'),
                        html.P("👆 Haz clic en cualquier barra para ver los productos más vendidos en ese día",
                               className="text-info text-center small mt-2")
                    ])
                ]), width=6)
            ]),

        ], label="⏰ HORAS"),

        # TAB 5: EVENTOS ESPECIALES
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎉 EVENTOS ESPECIALES", className="bg-danger text-white fw-bold"),
                        dbc.CardBody([
                            html.P(f"📊 {len(eventos_con_datos)} eventos con datos", className="text-center mb-3"),
                            dbc.Row(id='botones-eventos', className="g-2 mb-4"),
                            html.Hr(),
                            html.Div(id='resultado-eventos', className="mt-4")
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="🎉 EVENTOS"),

        # TAB 6: PRODUCTOS COMPLEMENTARIOS
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔄 PRODUCTOS COMPLEMENTARIOS", className="bg-purple text-white fw-bold", style={'backgroundColor': '#6f42c1'}),
                        dbc.CardBody([
                            html.P("¿Qué productos se compran juntos?", className="lead"),
                            html.Div(id='prod-comp'),
                            html.Hr(),
                            html.H5("📊 Estrategia de Venta Cruzada"),
                            html.P([
                                "Este análisis permite identificar oportunidades de venta cruzada. ",
                                "Los productos que aparecen juntos con frecuencia pueden ofrecerse como ",
                                "bundles o sugerirse durante el checkout para aumentar el ticket promedio."
                            ])
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ]),

        ], label="🔄 COMPLEMENTOS"),

        # TAB 7: PROPUESTAS ESTRATÉGICAS
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📋 PROPUESTAS ESTRATÉGICAS 2020", className="bg-dark text-white fw-bold"),
                        dbc.CardBody(id='propuestas-content')
                    ], className="shadow-sm")
                ], width=12)
            ]),

        ], label="📋 PROPUESTAS"),

    ], className="mb-4"),

    # Modales interactivos
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-horas-titulo")),
        dbc.ModalBody(id="modal-horas-contenido"),
        dbc.ModalFooter(dbc.Button("Cerrar", id="cerrar-modal-horas", className="ms-auto")),
    ], id="modal-horas", size="xl"),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-dias-titulo")),
        dbc.ModalBody(id="modal-dias-contenido"),
        dbc.ModalFooter(dbc.Button("Cerrar", id="cerrar-modal-dias", className="ms-auto")),
    ], id="modal-dias", size="xl"),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-ingresos-hora-titulo")),
        dbc.ModalBody(id="modal-ingresos-hora-contenido"),
        dbc.ModalFooter(dbc.Button("Cerrar", id="cerrar-modal-ingresos-hora", className="ms-auto")),
    ], id="modal-ingresos-hora", size="xl"),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.Div([
                html.Span("📊 Desarrollado por: Paola Dueña - Data Analyst | ", className="text-muted small"),
                html.A(" LinkedIn", href="https://ar.linkedin.com/in/paoladit", target="_blank", className="text-primary small"),
                html.Span(" | ", className="text-muted small"),
                html.A(" paoladf.it@gmail.com", href="mailto:paoladf.it@gmail.com", className="text-primary small"),
                html.Br(),
                html.Span(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}", className="text-muted small"),
            ], className="text-center")
        ], width=12)
    ], className="mt-4"),

], fluid=True)

# =============================================================================
# 17. CALLBACKS
# =============================================================================

@callback(
    [Output('ciudad', 'options'),
     Output('ciudad', 'value')],
    [Input('estado', 'value'),
     Input('reset', 'n_clicks')]
)
def update_ciudades(estado, reset):
    """
    Actualiza las opciones de ciudades basado en el estado seleccionado.
    """
    ctx = dash.callback_context
    if ctx.triggered and 'reset' in ctx.triggered[0]['prop_id']:
        return [{'label': 'Todas', 'value': 'Todas'}] + [{'label': c, 'value': c} for c in sorted(df['Ciudad'].unique())], 'Todas'

    if estado == 'Todos':
        ciudades = ['Todas'] + sorted(df['Ciudad'].unique())
    else:
        ciudades = ['Todas'] + sorted(df[df['Estado Nombre'] == estado]['Ciudad'].unique())
    return [{'label': c, 'value': c} for c in ciudades], 'Todas'

@callback(
    [Output('estado', 'value'),
     Output('mes', 'value'),
     Output('dia', 'value'),
     Output('categoria', 'value'),
     Output('rango', 'value'),
     Output('fechas', 'start_date'),
     Output('fechas', 'end_date'),
     Output('filtro-prod', 'value'),
     Output('comp-meses', 'value')],
    Input('reset', 'n_clicks')
)
def reset_filtros(n_clicks):
    """
    Restablece todos los filtros a sus valores por defecto.
    """
    if not n_clicks:
        return [no_update] * 9
    return ('Todos', 'Todos', 'Todos', 'Todas', 'Todos',
            df['Fecha'].min(), df['Fecha'].max(), 'General', ['Enero', 'Febrero', 'Marzo'])

@callback(
    Output('propuestas-content', 'children'),
    Input('propuestas-content', 'id')
)
def generar_propuestas(_):
    """
    Genera el contenido de la pestaña de propuestas estratégicas.
    """
    return html.Div([
        html.H4("🎯 RESUMEN EJECUTIVO", className="text-primary mt-4"),
        dbc.Table(
            html.Tbody([
                html.Tr([html.Td("📈 Crecimiento anual"), html.Td(f"+{CRECIMIENTO_ANUAL:.1f}%", className="text-success fw-bold"), html.Td("Excelente desempeño")]),
                html.Tr([html.Td("💰 Ticket promedio"), html.Td(f"${TICKET_PROMEDIO:,.2f}", className="text-info fw-bold"), html.Td("Oportunidad de upselling")]),
                html.Tr([html.Td("⏰ Hora óptima"), html.Td(f"{HORA_OPTIMA}:00", className="text-warning fw-bold"), html.Td(RAZON_HORA)]),
                html.Tr([html.Td("📆 Mejor día"), html.Td(f"{DIA_PICO}", className="text-danger fw-bold"), html.Td("Patrón de compra")]),
                html.Tr([html.Td("🏆 Producto estrella"), html.Td(PRODUCTO_TOP[:30], className="text-success fw-bold"), html.Td("Líder en ventas")]),
                html.Tr([html.Td("📦 Categoría top"), html.Td(CATEGORIA_TOP, className="text-primary fw-bold"), html.Td("Segmento clave")]),
            ]),
            bordered=True, size="sm", className="mb-3"
        ),
        html.Hr(),

        dbc.Card([
            dbc.CardHeader([html.H5("📋 PROPUESTA 1: OPTIMIZACIÓN PUBLICITARIA"), dbc.Badge("ROI 300%", color="success", className="ms-2"), html.Span(" | Inversión: $50,000", className="ms-2 text-muted small")], className="bg-light"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("🔍 PROBLEMA", className="text-danger"),
                        html.P("Inversión publicitaria sin considerar patrones de compra."),
                        html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                        html.Ul([html.Li(f"⏰ Hora óptima: {HORA_OPTIMA}:00"), html.Li(f"📆 Mejor día: {DIA_PICO}")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li(f"📈 Aumentar ads: {DIA_PICO} {max(0, HORA_OPTIMA - 2)}-{min(23, HORA_OPTIMA + 2)}h"),
                                html.Li("⚡ Promociones relámpago en horas pico")]),
                        html.H6("📈 RESULTADOS ESPERADOS", className="text-info mt-3"),
                        html.P("💰 ROI 300%: Por cada $1 invertido, ganarás $3 netos."),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-primary border-4"),

        dbc.Card([
            dbc.CardHeader([html.H5("📦 PROPUESTA 2: VENTA CRUZADA"), dbc.Badge("ROI 500%", color="success", className="ms-2"), html.Span(" | Inversión: $20,000", className="ms-2 text-muted small")], className="bg-light"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("🔍 PROBLEMA", className="text-danger"),
                        html.P("Productos económicos tienen ticket bajo."),
                        html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                        html.Ul([html.Li("📱 iPhone + AirPods: +35% ticket"),
                                html.Li(f"🔋 {PRODUCTO_TOP[:30]}: producto estrella")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li("💡 Sugerir complementarios en checkout"),
                                html.Li("📦 Crear bundles con productos estrella")]),
                        html.H6("📈 RESULTADOS ESPERADOS", className="text-info mt-3"),
                        html.P("💰 ROI 500%: Por cada $1 invertido, ganarás $5 netos."),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-success border-4"),

        dbc.Card([
            dbc.CardHeader([html.H5("📅 PROPUESTA 3: CALENDARIO DE PROMOCIONES"), dbc.Badge("ROI 400%", color="success", className="ms-2"), html.Span(" | Inversión: $30,000", className="ms-2 text-muted small")], className="bg-light"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("🔍 PROBLEMA", className="text-danger"),
                        html.P("Patrones estacionales no aprovechados."),
                        html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                        html.Ul([html.Li("🎉 Black Friday: +185%"), html.Li("🎄 Navidad: +210%")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li("📅 Enero: Liquidación de temporada"),
                                html.Li("🎁 Nov-Dic: Envío garantizado antes de fiestas")]),
                        html.H6("📈 RESULTADOS ESPERADOS", className="text-info mt-3"),
                        html.P("💰 ROI 400%: Por cada $1 invertido, ganarás $4 netos."),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-warning border-4"),
    ])

@callback(
    Output('botones-eventos', 'children'),
    Input('botones-eventos', 'id')
)
def crear_botones_eventos(_):
    """
    Crea los botones para cada evento especial con datos.
    """
    colores = ['primary', 'success', 'danger', 'warning', 'info', 'secondary']
    return [
        dbc.Col(
            dbc.Button(
                evento,
                id=f'btn-evento-{i}',
                color=colores[i % len(colores)],
                className="w-100 mb-2",
                n_clicks=0
            ),
            width=3
        ) for i, evento in enumerate(eventos_con_datos)
    ]

# =============================================================================
# CALLBACK PARA EVENTOS
# =============================================================================
@callback(
    Output("resultado-eventos", "children"),
    [Input(f'btn-evento-{i}', 'n_clicks') for i in range(len(eventos_con_datos))],
    prevent_initial_call=True
)
def mostrar_evento(*args):
    """
    Muestra los detalles del evento seleccionado.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        return html.P("Haz clic en un botón para ver los detalles del evento")

    boton_id = ctx.triggered[0]['prop_id'].split('.')[0]
    indice = int(boton_id.replace('btn-evento-', ''))
    evento_nombre = eventos_con_datos[indice]

    data_evento = df[df['Evento'] == evento_nombre]

    if data_evento.empty:
        return html.Div([
            dbc.Alert(f"No hay datos para {evento_nombre}", color="warning")
        ])

    total_ingresos = data_evento['Ingreso Total'].sum()
    total_pedidos = data_evento['ID de Pedido'].nunique()
    total_unidades = data_evento['Cantidad Pedida'].sum()
    ticket_promedio = total_ingresos / total_pedidos if total_pedidos > 0 else 0

    top_productos = data_evento.groupby('Producto')['Cantidad Pedida'].sum().nlargest(5).reset_index()
    top_productos.columns = ['Producto', 'Unidades Vendidas']

    # Comparación con día normal
    data_normal = df[df['Evento'] == 'Normal']
    if not data_normal.empty:
        ventas_por_dia_normal = data_normal.groupby('Fecha')['Ingreso Total'].sum().mean()
        incremento = ((total_ingresos / ventas_por_dia_normal) - 1) * 100 if ventas_por_dia_normal > 0 else 0
    else:
        incremento = 0

    if incremento > 50:
        color = "success"
        icono = "🚀"
        mensaje = "¡Excelente!"
    elif incremento > 20:
        color = "info"
        icono = "📈"
        mensaje = "Muy bueno"
    elif incremento > 0:
        color = "primary"
        icono = "👍"
        mensaje = "Bueno"
    elif incremento > -20:
        color = "warning"
        icono = "👎"
        mensaje = "Regular"
    else:
        color = "danger"
        icono = "📉"
        mensaje = "Malo"

    resultado = html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H3(f"{icono} {evento_nombre}", className=f"text-{color} d-inline"),
                html.H5(f"{mensaje} ({incremento:+.1f}% vs día normal)", className=f"text-{color} float-end")
            ], className=f"bg-light"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("💰 Ingresos Totales", className="text-center text-muted"),
                            html.H3(f"${total_ingresos:,.0f}", className="text-center text-primary")
                        ])
                    ]), width=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("📦 Pedidos", className="text-center text-muted"),
                            html.H3(f"{total_pedidos:,}", className="text-center text-success")
                        ])
                    ]), width=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("📊 Unidades", className="text-center text-muted"),
                            html.H3(f"{total_unidades:,}", className="text-center text-info")
                        ])
                    ]), width=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("🎫 Ticket Promedio", className="text-center text-muted"),
                            html.H3(f"${ticket_promedio:,.2f}", className="text-center text-warning")
                        ])
                    ]), width=3),
                ], className="mb-3"),
                html.H5("🏆 Top 5 Productos Más Vendidos"),
                dbc.Table.from_dataframe(top_productos, striped=True, bordered=True, hover=True, size="sm"),
            ])
        ])
    ])

    return resultado

# =============================================================================
# CALLBACKS DE EXPORTACIÓN
# =============================================================================

@callback(
    Output("download-csv", "data"),
    Input("btn-csv", "n_clicks"),
    [State('ciudad', 'value'),
     State('estado', 'value'),
     State('mes', 'value'),
     State('dia', 'value'),
     State('categoria', 'value'),
     State('rango', 'value'),
     State('fechas', 'start_date'),
     State('fechas', 'end_date')],
    prevent_initial_call=True
)
def exportar_csv(n_clicks, ciudad, estado, mes, dia, categoria, rango, start, end):
    """
    Exporta los datos visibles a CSV.
    """
    if not n_clicks:
        raise PreventUpdate

    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)
    csv_content = generar_csv_datos_visibles(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return dcc.send_string(
        csv_content,
        f"analisis_ventas_{timestamp}.csv"
    )

@callback(
    Output("download-excel", "data"),
    Input("btn-excel", "n_clicks"),
    [State('ciudad', 'value'),
     State('estado', 'value'),
     State('mes', 'value'),
     State('dia', 'value'),
     State('categoria', 'value'),
     State('rango', 'value'),
     State('fechas', 'start_date'),
     State('fechas', 'end_date')],
    prevent_initial_call=True
)
def exportar_excel(n_clicks, ciudad, estado, mes, dia, categoria, rango, start, end):
    """
    Exporta los datos visibles a Excel.
    """
    if not n_clicks:
        raise PreventUpdate

    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)
    excel_base64 = generar_excel_datos_visibles(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if excel_base64:
        return dcc.send_bytes(
            base64.b64decode(excel_base64),
            f"analisis_ventas_{timestamp}.xlsx"
        )
    raise PreventUpdate

@callback(
    [Output("download-pdf", "data"),
     Output("download-informe", "data")],
    [Input("btn-pdf", "n_clicks"),
     Input("btn-informe", "n_clicks")],
    [State('ciudad', 'value'),
     State('estado', 'value'),
     State('mes', 'value'),
     State('dia', 'value'),
     State('categoria', 'value'),
     State('rango', 'value'),
     State('fechas', 'start_date'),
     State('fechas', 'end_date')],
    prevent_initial_call=True
)
def exportar_pdf(btn_pdf, btn_informe, ciudad, estado, mes, dia, categoria, rango, start, end):
    """
    Exporta los datos visibles a PDF.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if 'btn-pdf' in ctx.triggered[0]['prop_id']:
        titulo = "Informe de Ventas - Análisis Visual"
        filename = f"informe_visual_{timestamp}.pdf"
    else:
        titulo = "Informe Completo de Ventas 2019"
        filename = f"informe_completo_{timestamp}.pdf"

    pdf_base64 = generar_informe_pdf_datos_visibles(data, titulo)

    if pdf_base64:
        if 'btn-pdf' in ctx.triggered[0]['prop_id']:
            return dcc.send_bytes(base64.b64decode(pdf_base64), filename), no_update
        else:
            return no_update, dcc.send_bytes(base64.b64decode(pdf_base64), filename)
    raise PreventUpdate

# =============================================================================
# CALLBACK PRINCIPAL
# =============================================================================
@callback(
    [Output('subtitulo', 'children'),
     Output('kpis', 'children'),
     Output('tendencias', 'children'),
     Output('graf-mes', 'figure'),
     Output('graf-tendencia', 'figure'),
     Output('graf-heatmap', 'figure'),
     Output('graf-dias', 'figure'),
     Output('graf-ciudades', 'figure'),
     Output('mapa-estados', 'figure'),
     Output('graf-estados-barras', 'figure'),
     Output('graf-categorias', 'figure'),
     Output('graf-estados-mensual', 'figure'),
     Output('titulo-variacion', 'children'),
     Output('resumen', 'children'),
     Output('prod-container', 'children'),
     Output('tabla-prod-mes', 'children'),
     Output('factores-prod', 'children'),
     Output('graf-horas-dist', 'figure'),
     Output('graf-ingresos-hora', 'figure'),
     Output('graf-horas-heat', 'figure'),
     Output('graf-comp-tend', 'figure'),
     Output('graf-comp-dist', 'figure'),
     Output('comp-kpis', 'children'),
     Output('comp-tabla', 'children'),
     Output('comp-productos', 'children'),
     Output('prod-comp', 'children')],
    [Input('ciudad', 'value'),
     Input('estado', 'value'),
     Input('mes', 'value'),
     Input('dia', 'value'),
     Input('categoria', 'value'),
     Input('rango', 'value'),
     Input('fechas', 'start_date'),
     Input('fechas', 'end_date'),
     Input('filtro-prod', 'value'),
     Input('comp-meses', 'value'),
     Input('comp-metrica', 'value')]
)
def update_dashboard(ciudad, estado, mes, dia, categoria, rango, start, end, filtro_prod, meses_comp, metrica):
    """
    Actualiza todos los componentes del dashboard basado en los filtros seleccionados.
    """
    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)

    subtitulo = f"📊 {len(data):,} transacciones | {data['Ciudad'].nunique()} ciudades | {data['Categoría'].nunique()} categorías"

    empty_fig = go.Figure().add_annotation(text="Sin datos", showarrow=False)
    empty_fig.update_layout(height=300)

    if data.empty:
        empty_kpi = dbc.Row([dbc.Col(html.H4("No hay datos para los filtros seleccionados"), width=12)])
        empty_tendencias = html.P("Sin datos")
        empty_resumen = html.P("Sin datos")
        empty_container = html.P("Sin datos")
        empty_table = html.P("Sin datos")
        empty_factores = html.P("Sin datos")

        return (subtitulo, empty_kpi, empty_tendencias, empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, "Sin datos", empty_resumen,
                empty_container, empty_table, empty_factores,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_table, empty_table, empty_fig)

    # =========================================================================
    # KPIs
    # =========================================================================
    ingresos = data['Ingreso Total'].sum()
    pedidos = data['ID de Pedido'].nunique()
    unidades = data['Cantidad Pedida'].sum()
    ticket = ingresos / pedidos if pedidos > 0 else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("💰 INGRESOS"), html.H3(f"${ingresos:,.0f}")])], className="border-primary"), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 PEDIDOS"), html.H3(f"{pedidos:,}")])], className="border-success"), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🎫 TICKET"), html.H3(f"${ticket:,.2f}")])], className="border-info"), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏙️ CIUDADES"), html.H3(f"{data['Ciudad'].nunique()}")])], className="border-warning"), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 CATEGORÍAS"), html.H3(f"{data['Categoría'].nunique()}")])], className="border-danger"), width=2),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📊 ESTADOS"), html.H3(f"{data['Estado Nombre'].nunique()}")])], className="border-secondary"), width=2),
    ])

    # =========================================================================
    # Tendencias
    # =========================================================================
    crecimiento = 0
    if len(data.groupby('Mes Num')['Ingreso Total'].sum()) > 1:
        ventas_mes = data.groupby('Mes Num')['Ingreso Total'].sum()
        crecimiento = ((ventas_mes.iloc[-1] / ventas_mes.iloc[0] - 1) * 100)

    hora_pico = data.groupby('Hora')['ID de Pedido'].nunique().idxmax()
    dia_pico = data.groupby('Día Semana Nombre')['ID de Pedido'].nunique().idxmax()
    prod_top = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
    cat_top = data.groupby('Categoría')['Ingreso Total'].sum().idxmax()

    color_crec = "success" if crecimiento > 0 else "danger" if crecimiento < 0 else "warning"
    signo = "+" if crecimiento > 0 else ""

    tendencias = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📈 CRECIMIENTO"), html.H3(f"{signo}{crecimiento:.1f}%", className=f"text-{color_crec}")])], className="bg-light"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("⏰ HORA PICO"), html.H3(f"{hora_pico}:00", className="text-warning")])], className="bg-light"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📆 MEJOR DÍA"), html.H3(dia_pico, className="text-info")])], className="bg-light"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏆 CATEGORÍA"), html.H6(cat_top[:15], className="text-success")])], className="bg-light"), width=3),
    ])

    # =========================================================================
    # Ventas por mes
    # =========================================================================
    df_mes = data.groupby('Mes')['Ingreso Total'].sum().reindex(MESES).reset_index()
    df_mes = df_mes.fillna(0)
    df_mes.columns = ['Mes', 'Ingreso Total']

    fig_mes = px.bar(df_mes, x='Mes', y='Ingreso Total', title='💰 Ventas por Mes',
                     color='Ingreso Total', color_continuous_scale='Blues', text_auto='.2s')
    fig_mes.update_traces(texttemplate='$%{text:.2s}', textposition='outside')

    # =========================================================================
    # Tendencia diaria
    # =========================================================================
    diario = data.groupby('Fecha')['Ingreso Total'].sum().reset_index()
    diario['Fecha'] = pd.to_datetime(diario['Fecha'])
    diario = diario.sort_values('Fecha')

    fig_tendencia = go.Figure()
    fig_tendencia.add_trace(go.Scatter(x=diario['Fecha'], y=diario['Ingreso Total'],
                                       mode='lines', line=dict(color='#8e44ad', width=2)))
    fig_tendencia.update_layout(title='📈 Tendencia Diaria', xaxis_title='Fecha', yaxis_title='Ingresos ($)')

    # =========================================================================
    # Heatmap día vs hora
    # =========================================================================
    fig_heatmap = px.density_heatmap(data, x='Hora', y='Día Semana Nombre', z='Ingreso Total',
                                     title='🔥 Mapa de Calor - Ingresos por Hora y Día',
                                     color_continuous_scale='Viridis',
                                     labels={'Hora': 'Hora del Día', 'Día Semana Nombre': 'Día'})

    # =========================================================================
    # Ventas por día
    # =========================================================================
    dias_df = data.groupby('Día Semana Nombre')['ID de Pedido'].nunique().reindex(DIAS).reset_index()
    dias_df.columns = ['Día', 'Pedidos']
    dias_df = dias_df.fillna(0)

    colores_dias = ['#3498db'] * 5 + ['#e74c3c'] * 2
    fig_dias = px.bar(dias_df, x='Día', y='Pedidos', title='📆 Ventas por Día',
                      color_discrete_sequence=colores_dias)
    fig_dias.update_traces(texttemplate='%{y}', textposition='outside')

    # =========================================================================
    # Top ciudades
    # =========================================================================
    top_ciud = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
    fig_ciudades = px.bar(top_ciud, x='Ingreso Total', y='Ciudad', orientation='h',
                          title='🏙️ Top 10 Ciudades', color='Ingreso Total',
                          color_continuous_scale='Reds',
                          text=top_ciud['Ingreso Total'].apply(lambda x: f'${x:,.0f}'))
    fig_ciudades.update_traces(texttemplate='%{text}', textposition='outside')

    # =========================================================================
    # Mapa de estados con nombres visibles
    # =========================================================================
    ventas_estado = data.groupby('Estado Nombre')['Ingreso Total'].sum().reset_index()
    ventas_estado['codigo'] = ventas_estado['Estado Nombre'].map(nombre_a_codigo).fillna('NA')

    fig_mapa = go.Figure()

    fig_mapa.add_trace(go.Choropleth(
        locations=ventas_estado['codigo'],
        z=ventas_estado['Ingreso Total'],
        locationmode='USA-states',
        colorscale='Reds',
        colorbar_title="Ingresos ($)",
        text=ventas_estado['Estado Nombre'],
        hovertemplate='<b>%{text}</b><br>Ingresos: $%{z:,.0f}<extra></extra>',
        showscale=True,
        marker_line_color='white',
        marker_line_width=0.5
    ))

    # Coordenadas para nombres de estados
    coords_nombres = {
        'Alabama': {'lon': -86.5, 'lat': 32.5}, 'Arizona': {'lon': -111.5, 'lat': 34.5},
        'Arkansas': {'lon': -92.5, 'lat': 34.5}, 'California': {'lon': -119.5, 'lat': 37.5},
        'Colorado': {'lon': -105.5, 'lat': 39.5}, 'Connecticut': {'lon': -72.5, 'lat': 41.5},
        'Delaware': {'lon': -75.5, 'lat': 39.5}, 'Florida': {'lon': -81.5, 'lat': 28.5},
        'Georgia': {'lon': -83.5, 'lat': 32.5}, 'Idaho': {'lon': -114.5, 'lat': 45.5},
        'Illinois': {'lon': -89.5, 'lat': 40.5}, 'Indiana': {'lon': -86.5, 'lat': 40.5},
        'Iowa': {'lon': -93.5, 'lat': 42.5}, 'Kansas': {'lon': -98.5, 'lat': 38.5},
        'Kentucky': {'lon': -84.5, 'lat': 37.5}, 'Louisiana': {'lon': -91.5, 'lat': 31.5},
        'Maine': {'lon': -69.5, 'lat': 45.5}, 'Maryland': {'lon': -76.5, 'lat': 39.5},
        'Massachusetts': {'lon': -71.5, 'lat': 42.5}, 'Michigan': {'lon': -85.5, 'lat': 44.5},
        'Minnesota': {'lon': -94.5, 'lat': 46.5}, 'Mississippi': {'lon': -89.5, 'lat': 32.5},
        'Missouri': {'lon': -92.5, 'lat': 38.5}, 'Montana': {'lon': -110.5, 'lat': 47.5},
        'Nebraska': {'lon': -99.5, 'lat': 41.5}, 'Nevada': {'lon': -117.5, 'lat': 39.5},
        'New Hampshire': {'lon': -71.5, 'lat': 44.5}, 'New Jersey': {'lon': -74.5, 'lat': 40.5},
        'New Mexico': {'lon': -106.5, 'lat': 34.5}, 'Nueva York': {'lon': -75.5, 'lat': 42.5},
        'North Carolina': {'lon': -79.5, 'lat': 35.5}, 'North Dakota': {'lon': -100.5, 'lat': 47.5},
        'Ohio': {'lon': -82.5, 'lat': 40.5}, 'Oklahoma': {'lon': -97.5, 'lat': 35.5},
        'Oregon': {'lon': -120.5, 'lat': 44.5}, 'Pennsylvania': {'lon': -77.5, 'lat': 41.5},
        'Rhode Island': {'lon': -71.5, 'lat': 41.5}, 'South Carolina': {'lon': -80.5, 'lat': 34.5},
        'South Dakota': {'lon': -100.5, 'lat': 44.5}, 'Tennessee': {'lon': -86.5, 'lat': 35.5},
        'Texas': {'lon': -99.5, 'lat': 31.5}, 'Utah': {'lon': -111.5, 'lat': 40.5},
        'Vermont': {'lon': -72.5, 'lat': 44.5}, 'Virginia': {'lon': -78.5, 'lat': 37.5},
        'Washington': {'lon': -120.5, 'lat': 47.5}, 'West Virginia': {'lon': -80.5, 'lat': 38.5},
        'Wisconsin': {'lon': -89.5, 'lat': 44.5}, 'Wyoming': {'lon': -107.5, 'lat': 43.5},
    }

    nombres_lon, nombres_lat, nombres_text = [], [], []
    for _, row in ventas_estado.iterrows():
        estado_nombre = row['Estado Nombre']
        if estado_nombre in coords_nombres and estado_nombre not in ['Alaska', 'Hawaii']:
            nombres_lon.append(coords_nombres[estado_nombre]['lon'])
            nombres_lat.append(coords_nombres[estado_nombre]['lat'])
            nombres_text.append(estado_nombre)

    fig_mapa.add_trace(go.Scattergeo(
        lon=nombres_lon, lat=nombres_lat, text=nombres_text,
        mode='text', textfont=dict(size=10, color='black', family='Arial Black'),
        textposition='middle center', showlegend=False, hoverinfo='none'
    ))

    fig_mapa.update_layout(
        title=dict(text='🗺️ Ventas por Estado', x=0.5, font=dict(size=16)),
        geo=dict(scope='usa', projection=dict(type='albers usa'), showlakes=True, lakecolor='rgb(255,255,255)'),
        height=500, margin=dict(l=0, r=0, t=40, b=0)
    )

    # =========================================================================
    # Barras de estados
    # =========================================================================
    ventas_estado_ordenado = ventas_estado.sort_values('Ingreso Total', ascending=True).tail(15)
    fig_estados_barras = px.bar(ventas_estado_ordenado, x='Ingreso Total', y='Estado Nombre',
                                orientation='h', title='📊 Ventas por Estado', color='Ingreso Total',
                                color_continuous_scale='Reds',
                                text=ventas_estado_ordenado['Ingreso Total'].apply(lambda x: f'${x:,.0f}'))
    fig_estados_barras.update_traces(texttemplate='%{text}', textposition='outside')

    # =========================================================================
    # Gráfico de categorías
    # =========================================================================
    ventas_cat = data.groupby('Categoría')['Ingreso Total'].sum().reset_index()
    ventas_cat = ventas_cat.sort_values('Ingreso Total', ascending=True)
    fig_categorias = px.bar(ventas_cat, x='Ingreso Total', y='Categoría', orientation='h',
                            title='📦 Ventas por Categoría', color='Ingreso Total',
                            color_continuous_scale='Viridis',
                            text=ventas_cat['Ingreso Total'].apply(lambda x: f'${x:,.0f}'))
    fig_categorias.update_traces(texttemplate='%{text}', textposition='outside')

    # =========================================================================
    # Variación mensual
    # =========================================================================
    ventas_estado_mes = data.groupby(['Estado Nombre', 'Mes'])['Ingreso Total'].sum().reset_index()

    # Determinar el título correcto
    if estado != 'Todos' and estado in ventas_estado['Estado Nombre'].values:
        titulo_variacion = f"📊 Evolución Mensual: {estado}"
    else:
        titulo_variacion = "📊 Variación Mensual por Estado (Top 5)"

    # Generar el gráfico
    if estado != 'Todos' and estado in ventas_estado['Estado Nombre'].values:
        df_estado = ventas_estado_mes[ventas_estado_mes['Estado Nombre'] == estado]
        fig_estados_mensual = px.line(df_estado, x='Mes', y='Ingreso Total', markers=True,
                                      title=titulo_variacion, color_discrete_sequence=['#e74c3c'])
    else:
        top_estados = data.groupby('Estado Nombre')['Ingreso Total'].sum().nlargest(5).index
        fig_estados_mensual = go.Figure()
        for i, e in enumerate(top_estados):
            df_e = ventas_estado_mes[ventas_estado_mes['Estado Nombre'] == e]
            if not df_e.empty:
                fig_estados_mensual.add_trace(go.Scatter(
                    x=df_e['Mes'], y=df_e['Ingreso Total'],
                    mode='lines+markers', name=e,
                    line=dict(color=COLORES[i % len(COLORES)], width=3),
                    marker=dict(size=8)
                ))
        fig_estados_mensual.update_layout(title=titulo_variacion)

    fig_estados_mensual.update_layout(
        xaxis_title='Mes', yaxis_title='Ingresos ($)',
        hovermode='x unified', height=400
    )

    # =========================================================================
    # Resumen
    # =========================================================================
    resumen = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏆 Producto"), html.P(PRODUCTO_TOP[:20], className="text-success")])], className="border-success"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏙️ Ciudad"), html.P(CIUDAD_TOP[:20], className="text-primary")])], className="border-primary"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🗺️ Estado"), html.P(ESTADO_TOP[:20], className="text-info")])], className="border-info"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 Categoría"), html.P(CATEGORIA_TOP, className="text-warning")])], className="border-warning"), width=3),
    ])

    # =========================================================================
    # Producto estrella
    # =========================================================================
    if filtro_prod == 'General':
        analisis = analizar_producto_estrella(data, "GLOBAL")
    elif filtro_prod == 'Mes':
        if mes != 'Todos':
            analisis = analizar_producto_estrella(data[data['Mes'] == mes], f"MES: {mes}")
        else:
            mtop = data.groupby('Mes')['Cantidad Pedida'].sum().idxmax()
            analisis = analizar_producto_estrella(data[data['Mes'] == mtop], f"MES: {mtop} (top)")
    elif filtro_prod == 'Semana':
        stop = data.groupby('Semana')['Cantidad Pedida'].sum().idxmax()
        analisis = analizar_producto_estrella(data[data['Semana'] == stop], f"SEMANA: {stop}")
    else:
        dtop = data.groupby('Día del Año')['Cantidad Pedida'].sum().idxmax()
        analisis = analizar_producto_estrella(data[data['Día del Año'] == dtop], "DÍA PICO")

    if analisis:
        prod_container = dbc.Card([
            dbc.CardBody([
                html.H4("🏆 PRODUCTO ESTRELLA", className="text-center text-primary mb-3", style={'fontWeight': 'bold'}),
                html.Div([
                    html.H3(analisis['producto'],
                           className="text-center text-success",
                           style={
                               'fontSize': '1.8rem', 'fontWeight': 'bold', 'wordBreak': 'break-word',
                               'whiteSpace': 'normal', 'lineHeight': '1.4', 'backgroundColor': '#f8f9fa',
                               'padding': '20px', 'borderRadius': '10px', 'border': '2px solid #28a745',
                               'marginBottom': '20px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                           })
                ]),
                dbc.Row([
                    dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 Unidades"), html.H4(f"{analisis['unidades']:,.0f}")])], className="border-primary"), width=4),
                    dbc.Col(dbc.Card([dbc.CardBody([html.H6("💰 Ingresos"), html.H4(f"${analisis['ingresos']:,.0f}")])], className="border-success"), width=4),
                    dbc.Col(dbc.Card([dbc.CardBody([html.H6("📊 Participación"), html.H4(f"{analisis['share']:.1f}%", title="% del total de unidades vendidas")])], className="border-info"), width=4),
                ], className="mb-3"),
                html.P(f"📌 Basado en: {analisis['filtro_aplicado']}", className="text-muted text-center mt-2")
            ])
        ], className="shadow-sm border-2 border-success mb-4")

        factores = dbc.Card([
            dbc.CardHeader("🔍 ANÁLISIS DETALLADO", className="bg-info text-white fw-bold text-center"),
            dbc.CardBody([
                html.H6("📊 Insights:", className="fw-bold"),
                html.Ul([html.Li(i) for i in analisis['insights']]),
                html.H6("📍 Factores de éxito:", className="fw-bold mt-3"),
                html.Ul([html.Li(i) for i in analisis['factores_exito']])
            ])
        ], className="shadow-sm")
    else:
        prod_container = html.Div([html.H5("No hay datos suficientes", className="text-center text-muted")])
        factores = html.Div()

    # =========================================================================
    # Tabla producto por mes
    # =========================================================================
    prods_mes = data.groupby(['Mes', 'Producto'])['Cantidad Pedida'].sum().reset_index()
    idx = prods_mes.groupby('Mes')['Cantidad Pedida'].idxmax()
    top_mes = prods_mes.loc[idx].set_index('Mes').reindex(MESES).reset_index()

    tabla_rows = []
    for _, row in top_mes.iterrows():
        producto = row['Producto'] if not pd.isna(row['Producto']) else "Sin datos"
        producto_mostrar = producto[:27] + "..." if len(producto) > 30 else producto
        tabla_rows.append(html.Tr([
            html.Td(row['Mes']),
            html.Td(html.Span(producto_mostrar, title=producto, style={'cursor': 'help'})),
            html.Td(f"{row['Cantidad Pedida']:,.0f}" if not pd.isna(row['Cantidad Pedida']) else "0")
        ]))

    tabla_prod_mes = dbc.Table(
        [html.Thead(html.Tr([html.Th("Mes"), html.Th("Producto"), html.Th("Cantidad")])),
         html.Tbody(tabla_rows)],
        striped=True, bordered=True, size='sm', hover=True
    )

    # =========================================================================
    # Horas - Frecuencia
    # =========================================================================
    horas = data.groupby('Hora')['ID de Pedido'].nunique().reset_index(name='Pedidos')
    fig_horas_dist = px.bar(horas, x='Hora', y='Pedidos', title='📊 Frecuencia de Pedidos por Hora',
                            color='Pedidos', color_continuous_scale='Viridis')

    # =========================================================================
    # Horas - Ingresos
    # =========================================================================
    ingresos_hora = data.groupby('Hora')['Ingreso Total'].sum().reset_index(name='Ingresos')
    fig_ingresos_hora = px.bar(ingresos_hora, x='Hora', y='Ingresos', title='💰 Ingresos por Hora',
                               color='Ingresos', color_continuous_scale='Greens', text_auto='.2s')
    fig_ingresos_hora.update_traces(texttemplate='$%{text:.2s}', textposition='outside')

    # =========================================================================
    # Heatmap hora vs mes
    # =========================================================================
    heat_hm = data.groupby(['Mes', 'Hora']).size().reset_index(name='Pedidos')
    pivot = heat_hm.pivot(index='Mes', columns='Hora', values='Pedidos').fillna(0).reindex(MESES)
    fig_horas_heat = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale='Viridis',
        hovertemplate='Mes: %{y}<br>Hora: %{x}<br>Pedidos: %{z}<extra></extra>'
    ))
    fig_horas_heat.update_layout(title='🔥 Heatmap Hora vs Mes', height=400)

    # =========================================================================
    # Comparador - CON NOMBRES COMPLETOS DE PRODUCTOS
    # =========================================================================
    comp_kpis = html.P("Selecciona meses para comparar")
    fig_comp_tend = empty_fig
    fig_comp_dist = empty_fig
    comp_tabla = html.P("Selecciona meses")
    comp_productos = html.P("Selecciona meses")

    if meses_comp and len(meses_comp) > 0:
        meses_filtrados = [m for m in meses_comp if m in data['Mes'].unique()]
        if meses_filtrados:
            # KPIs
            filas = []
            for i in range(0, len(meses_filtrados), 3):
                cols = []
                for m in meses_filtrados[i:i + 3]:
                    dm = data[data['Mes'] == m]
                    ingresos_m = dm['Ingreso Total'].sum()
                    pedidos_m = dm['ID de Pedido'].nunique()

                    valor = f"${ingresos_m:,.0f}" if metrica == 'ingresos' else f"{pedidos_m:,}"
                    cols.append(dbc.Col(dbc.Card(dbc.CardBody([html.H6(m), html.H4(valor, className="text-primary")])), width=4))
                filas.append(dbc.Row(cols, className="mb-2"))
            comp_kpis = html.Div(filas)

            # Gráficos
            fig_comp_tend = go.Figure()
            fig_comp_dist = go.Figure()
            colors = px.colors.qualitative.Set1

            for i, m in enumerate(meses_filtrados):
                dm = data[data['Mes'] == m]
                dia_df = dm.groupby('Día')['Ingreso Total'].sum().reset_index()
                fig_comp_tend.add_trace(go.Scatter(
                    x=dia_df['Día'], y=dia_df['Ingreso Total'],
                    mode='lines+markers', name=m,
                    line=dict(color=colors[i % len(colors)], width=3)
                ))

                horas_m = dm.groupby('Hora')['ID de Pedido'].nunique().reset_index(name='Pedidos')
                fig_comp_dist.add_trace(go.Scatter(
                    x=horas_m['Hora'], y=horas_m['Pedidos'],
                    mode='lines', name=m,
                    line=dict(color=colors[i % len(colors)]),
                    fill='tonexty' if i == 0 else None
                ))

            fig_comp_tend.update_layout(
                title='📈 Tendencia Comparativa por Mes',
                xaxis_title='Día del Mes', yaxis_title='Ingresos ($)',
                hovermode='x unified'
            )
            fig_comp_dist.update_layout(
                title='📊 Patrón Horario por Mes',
                xaxis_title='Hora del Día', yaxis_title='Pedidos',
                hovermode='x unified', height=300
            )

            # Tablas - CON NOMBRES COMPLETOS DE PRODUCTOS
            rows = []
            prod_rows = []
            for m in meses_filtrados:
                dm = data[data['Mes'] == m]
                rows.append([m, f"${dm['Ingreso Total'].sum():,.0f}", f"{dm['ID de Pedido'].nunique():,}"])
                
                # Producto estrella con nombre COMPLETO (sin truncar)
                prod_top = dm.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
                prod_cant = dm.groupby('Producto')['Cantidad Pedida'].sum().max()
                prod_rows.append([m, prod_top, f"{prod_cant:,.0f}"])

            # Tabla comparativa detallada
            comp_tabla = dbc.Table(
                [
                    html.Thead(html.Tr([
                        html.Th("Mes", className="text-center", style={'width': '20%'}),
                        html.Th("Ingresos", className="text-center", style={'width': '40%'}),
                        html.Th("Pedidos", className="text-center", style={'width': '40%'})
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row[0], className="text-center align-middle fw-bold"),
                            html.Td(row[1], className="text-end align-middle fw-bold text-success"),
                            html.Td(row[2], className="text-end align-middle fw-bold text-primary")
                        ]) for row in rows
                    ])
                ],
                striped=True,
                bordered=True,
                hover=True,
                size="sm",
                className="mt-2 shadow-sm"
            )

            # Tabla producto por mes - CON NOMBRES COMPLETOS
            comp_productos = dbc.Table(
                [
                    html.Thead(html.Tr([
                        html.Th("Mes", className="text-center", style={'width': '15%'}),
                        html.Th("Producto Estrella", className="text-center", style={'width': '65%'}),
                        html.Th("Unidades", className="text-center", style={'width': '20%'})
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row[0], className="text-center align-middle fw-bold"),
                            html.Td(row[1], className="align-middle", 
                                   style={'wordBreak': 'break-word', 'whiteSpace': 'normal', 'maxWidth': '300px'}),
                            html.Td(row[2], className="text-end align-middle fw-bold text-success")
                        ]) for row in prod_rows
                    ])
                ],
                striped=True,
                bordered=True,
                hover=True,
                size="sm",
                className="mt-2 shadow-sm"
            )

    # =========================================================================
    # Productos complementarios
    # =========================================================================
    top_pares = analizar_productos_complementarios(data)
    if top_pares:
        pares_rows = []
        for i, ((a, b), c) in enumerate(top_pares, 1):
            pares_rows.append(html.Tr([
                html.Td(f"#{i}", className="text-center fw-bold text-primary"),
                html.Td(a[:25]),
                html.Td(b[:25]),
                html.Td(f"{c} veces", className="text-end fw-bold text-success")
            ]))

        prod_comp = dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("#", className="text-center"),
                    html.Th("Producto A", className="text-center"),
                    html.Th("Producto B", className="text-center"),
                    html.Th("Frecuencia", className="text-center")
                ])),
                html.Tbody(pares_rows)
            ],
            striped=True,
            bordered=True,
            hover=True,
            size="sm",
            className="shadow-sm"
        )
    else:
        prod_comp = html.P("No se encontraron pares significativos", className="text-center text-muted fst-italic")

    return (subtitulo, kpis, tendencias, fig_mes, fig_tendencia, fig_heatmap, fig_dias,
            fig_ciudades, fig_mapa, fig_estados_barras, fig_categorias, fig_estados_mensual, titulo_variacion, resumen,
            prod_container, tabla_prod_mes, factores,
            fig_horas_dist, fig_ingresos_hora, fig_horas_heat,
            fig_comp_tend, fig_comp_dist, comp_kpis, comp_tabla, comp_productos,
            prod_comp)

# =============================================================================
# CALLBACKS PARA MODALES
# =============================================================================

@callback(
    [Output('modal-horas', 'is_open'),
     Output('modal-horas-titulo', 'children'),
     Output('modal-horas-contenido', 'children')],
    [Input('graf-horas-dist', 'clickData'),
     Input('cerrar-modal-horas', 'n_clicks')],
    [State('modal-horas', 'is_open'),
     State('fechas', 'start_date'), State('fechas', 'end_date'),
     State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'), State('dia', 'value'),
     State('categoria', 'value'), State('rango', 'value')]
)
def modal_horas(clickData, cerrar, is_open, start, end, ciudad, estado, mes, dia, categoria, rango):
    """
    Muestra un modal con detalles de la hora seleccionada en el gráfico de frecuencia.
    """
    ctx = dash.callback_context

    if ctx.triggered and 'cerrar-modal-horas' in ctx.triggered[0]['prop_id']:
        return False, "", html.P("")

    if not clickData:
        return False, "", html.P("")

    hora = clickData['points'][0]['x']
    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)
    data_hora = data[data['Hora'] == hora]

    if data_hora.empty:
        return True, f"⏰ Hora: {hora}:00", html.P("No hay datos para esta hora")

    top = data_hora.groupby('Producto').agg({
        'Cantidad Pedida': 'sum',
        'Ingreso Total': 'sum',
        'ID de Pedido': 'nunique'
    }).sort_values('Cantidad Pedida', ascending=False).head(10).reset_index()

    rows = []
    for _, r in top.iterrows():
        ticket = r['Ingreso Total'] / r['ID de Pedido'] if r['ID de Pedido'] > 0 else 0
        rows.append(html.Tr([
            html.Td(r['Producto'][:40]),
            html.Td(f"{r['Cantidad Pedida']:,.0f}", className="text-end fw-bold"),
            html.Td(f"${r['Ingreso Total']:,.0f}", className="text-end fw-bold text-success"),
            html.Td(f"${ticket:,.2f}", className="text-end fw-bold text-primary")
        ]))

    tabla = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Producto"),
            html.Th("Unidades", className="text-center"),
            html.Th("Ingresos", className="text-center"),
            html.Th("Ticket Prom", className="text-center")
        ])),
         html.Tbody(rows)],
        striped=True, bordered=True, hover=True, size='sm', className="shadow-sm"
    )

    total_unidades = data_hora['Cantidad Pedida'].sum()
    total_ingresos = data_hora['Ingreso Total'].sum()
    total_pedidos = data_hora['ID de Pedido'].nunique()
    promedio_hora = data['Cantidad Pedida'].sum() / 24 if len(data) > 0 else 0
    variacion = ((total_unidades / promedio_hora) - 1) * 100 if promedio_hora > 0 else 0
    color_variacion = "success" if variacion > 0 else "danger" if variacion < 0 else "secondary"

    return True, f"⏰ Análisis Detallado - Hora: {hora}:00", html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📦 Unidades Vendidas", className="text-center text-muted"),
                    html.H3(f"{total_unidades:,.0f}", className="text-center text-primary")
                ])
            ], className="border-primary shadow-sm"), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Ingresos Totales", className="text-center text-muted"),
                    html.H3(f"${total_ingresos:,.0f}", className="text-center text-success")
                ])
            ], className="border-success shadow-sm"), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📋 Total Pedidos", className="text-center text-muted"),
                    html.H3(f"{total_pedidos:,}", className="text-center text-info")
                ])
            ], className="border-info shadow-sm"), width=4),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📊 Comparación vs Promedio", className="text-center text-muted"),
                    html.H3([
                        html.Span(f"{variacion:+.1f}%", className=f"text-{color_variacion}"),
                        html.Small(" vs promedio por hora", className="text-muted ms-2")
                    ], className="text-center")
                ])
            ], className="border-warning shadow-sm"), width=12),
        ], className="mb-3"),
        html.H5(f"📦 Top 10 Productos Más Vendidos a las {hora}:00", className="mt-3 mb-3 text-primary"),
        tabla
    ])

@callback(
    [Output('modal-dias', 'is_open'),
     Output('modal-dias-titulo', 'children'),
     Output('modal-dias-contenido', 'children')],
    [Input('graf-dias', 'clickData'),
     Input('cerrar-modal-dias', 'n_clicks')],
    [State('modal-dias', 'is_open'),
     State('fechas', 'start_date'), State('fechas', 'end_date'),
     State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'), State('dia', 'value'),
     State('categoria', 'value'), State('rango', 'value')]
)
def modal_dias(clickData, cerrar, is_open, start, end, ciudad, estado, mes, dia, categoria, rango):
    """
    Muestra un modal con detalles del día seleccionado en el gráfico de ventas por día.
    """
    ctx = dash.callback_context

    if ctx.triggered and 'cerrar-modal-dias' in ctx.triggered[0]['prop_id']:
        return False, "", html.P("")

    if not clickData:
        return False, "", html.P("")

    dia_nombre = clickData['points'][0]['x']
    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)
    data_dia = data[data['Día Semana Nombre'] == dia_nombre]

    if data_dia.empty:
        return True, f"📆 Día: {dia_nombre}", html.P("No hay datos para este día")

    top = data_dia.groupby('Producto').agg({
        'Cantidad Pedida': 'sum',
        'Ingreso Total': 'sum',
        'ID de Pedido': 'nunique'
    }).sort_values('Cantidad Pedida', ascending=False).head(10).reset_index()

    rows = []
    for _, r in top.iterrows():
        rows.append(html.Tr([
            html.Td(r['Producto'][:40]),
            html.Td(f"{r['Cantidad Pedida']:,.0f}", className="text-end fw-bold"),
            html.Td(f"${r['Ingreso Total']:,.0f}", className="text-end fw-bold text-success"),
        ]))

    tabla = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Producto"),
            html.Th("Unidades", className="text-center"),
            html.Th("Ingresos", className="text-center")
        ])),
         html.Tbody(rows)],
        striped=True, bordered=True, hover=True, size='sm', className="shadow-sm"
    )

    total_unidades = data_dia['Cantidad Pedida'].sum()
    total_ingresos = data_dia['Ingreso Total'].sum()
    total_pedidos = data_dia['ID de Pedido'].nunique()
    tipo = "🏖️ FIN DE SEMANA" if dia_nombre in ['Sábado', 'Domingo'] else "💼 DÍA LABORABLE"
    color_tipo = "danger" if dia_nombre in ['Sábado', 'Domingo'] else "primary"

    hora_pico_data = data_dia.groupby('Hora')['ID de Pedido'].nunique()
    hora_pico = hora_pico_data.idxmax() if not hora_pico_data.empty else "N/A"

    return True, f"📆 Análisis Detallado - {dia_nombre}", html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📦 Unidades Vendidas", className="text-center text-muted"),
                    html.H3(f"{total_unidades:,.0f}", className="text-center text-primary")
                ])
            ], className="border-primary shadow-sm"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Ingresos Totales", className="text-center text-muted"),
                    html.H3(f"${total_ingresos:,.0f}", className="text-center text-success")
                ])
            ], className="border-success shadow-sm"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📋 Total Pedidos", className="text-center text-muted"),
                    html.H3(f"{total_pedidos:,}", className="text-center text-info")
                ])
            ], className="border-info shadow-sm"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📆 Tipo de Día", className="text-center text-muted"),
                    html.H6(tipo, className=f"text-center text-{color_tipo} fw-bold")
                ])
            ], className=f"border-{color_tipo} shadow-sm"), width=3),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("⏰ Hora Pico", className="text-center text-muted"),
                    html.H3(f"{hora_pico}:00", className="text-center text-warning")
                ])
            ], className="border-warning shadow-sm"), width=12),
        ], className="mb-3"),
        html.H5(f"📦 Top 10 Productos Más Vendidos los {dia_nombre}s", className="mt-3 mb-3 text-primary"),
        tabla
    ])

@callback(
    [Output('modal-ingresos-hora', 'is_open'),
     Output('modal-ingresos-hora-titulo', 'children'),
     Output('modal-ingresos-hora-contenido', 'children')],
    [Input('graf-ingresos-hora', 'clickData'),
     Input('cerrar-modal-ingresos-hora', 'n_clicks')],
    [State('modal-ingresos-hora', 'is_open'),
     State('fechas', 'start_date'), State('fechas', 'end_date'),
     State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'), State('dia', 'value'),
     State('categoria', 'value'), State('rango', 'value')]
)
def modal_ingresos_hora(clickData, cerrar, is_open, start, end, ciudad, estado, mes, dia, categoria, rango):
    """
    Muestra un modal con detalles de la hora seleccionada en el gráfico de ingresos por hora.
    """
    ctx = dash.callback_context

    if ctx.triggered and 'cerrar-modal-ingresos-hora' in ctx.triggered[0]['prop_id']:
        return False, "", html.P("")

    if not clickData:
        return False, "", html.P("")

    hora = clickData['points'][0]['x']
    data = obtener_datos_filtrados(ciudad, estado, mes, dia, categoria, rango, start, end)
    data_hora = data[data['Hora'] == hora]

    if data_hora.empty:
        return True, f"💰 Hora: {hora}:00", html.P("No hay datos para esta hora")

    top = data_hora.groupby('Producto')['Ingreso Total'].sum().nlargest(10).reset_index()
    rows = []
    for _, r in top.iterrows():
        rows.append(html.Tr([
            html.Td(r['Producto'][:40]),
            html.Td(f"${r['Ingreso Total']:,.0f}", className="text-end fw-bold text-success"),
        ]))

    tabla = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Producto"),
            html.Th("Ingresos", className="text-center")
        ])),
         html.Tbody(rows)],
        striped=True, bordered=True, hover=True, size='sm', className="shadow-sm"
    )

    total_ingresos = data_hora['Ingreso Total'].sum()
    total_unidades = data_hora['Cantidad Pedida'].sum()
    total_pedidos = data_hora['ID de Pedido'].nunique()
    ticket_promedio = total_ingresos / total_pedidos if total_pedidos > 0 else 0

    return True, f"💰 Análisis de Ingresos - Hora: {hora}:00", html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Ingresos Totales", className="text-center text-muted"),
                    html.H3(f"${total_ingresos:,.0f}", className="text-center text-success")
                ])
            ], className="border-success shadow-sm"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📦 Unidades Vendidas", className="text-center text-muted"),
                    html.H3(f"{total_unidades:,.0f}", className="text-center text-primary")
                ])
            ], className="border-primary shadow-sm"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📋 Total Pedidos", className="text-center text-muted"),
                    html.H3(f"{total_pedidos:,}", className="text-center text-info")
                ])
            ], className="border-info shadow-sm"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🎫 Ticket Promedio", className="text-center text-muted"),
                    html.H3(f"${ticket_promedio:,.2f}", className="text-center text-warning")
                ])
            ], className="border-warning shadow-sm"), width=3),
        ], className="mb-3"),
        html.H5(f"🏆 Top 10 Productos por Ingresos a las {hora}:00", className="mt-3 mb-3 text-primary"),
        tabla
    ])

# =============================================================================
# 18. EJECUCIÓN
# =============================================================================
def abrir_navegador():
    """
    Abre el navegador automáticamente después de iniciar el servidor.
    """
    webbrowser.open('http://127.0.0.1:8050')

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("✅ DASHBOARD INICIADO CORRECTAMENTE".center(80))
    print("=" * 80)
    print("\n🌐 Dirección local: http://127.0.0.1:8050")
    print(f"\n📊 Resumen de datos cargados:")
    print(f"   • {len(df):,} registros totales")
    print(f"   • ${TOTAL_INGRESOS:,.0f} en ingresos")
    print(f"   • {TOTAL_PEDIDOS:,} pedidos únicos")
    print(f"\n🎉 Eventos con datos ({len(eventos_con_datos)}):")
    for e in eventos_con_datos[:5]:  # Mostrar solo los primeros 5 para no saturar
        print(f"   • {e}: {len(df[df['Evento'] == e]):,} registros")
    if len(eventos_con_datos) > 5:
        print(f"   • ... y {len(eventos_con_datos) - 5} eventos más")

    print("\n✅ CARACTERÍSTICAS IMPLEMENTADAS:")
    print("   • 7 pestañas de análisis interactivo")
    print("   • Filtros globales por múltiples dimensiones")
    print("   • Exportación a CSV, Excel y PDF")
    print("   • Análisis de producto estrella con insights")
    print("   • Mapas interactivos con nombres de estados")
    print("   • Modales interactivos al hacer clic en gráficos")
    print("   • Propuestas estratégicas basadas en datos")
    print("   • Nombres completos de productos sin truncar ✓")

    print("\n" + "=" * 80)
    print("🚀 El dashboard se abrirá automáticamente en tu navegador".center(80))
    print("   Presiona Ctrl+C en la terminal para detener el servidor".center(80))
    print("=" * 80)

    threading.Timer(2, abrir_navegador).start()
    app.run(debug=False, port=8050)