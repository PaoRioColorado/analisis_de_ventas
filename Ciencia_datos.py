#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
                    PANEL DE VENTAS 2019 - VERSIÓN FINAL
================================================================================
Desarrollado por: Paola Dueña - Data Analyst
Versión: 50.1.0 - GRÁFICOS CORREGIDOS + MEJORAS
================================================================================
Mejoras implementadas:
    • Consistencia en filtros temporales
    • Nuevo gráfico de distribución en comparador
    • Análisis de variación mensual por estado
    • Documentación mejorada
================================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
warnings.filterwarnings('ignore')

print("="*80)
print("PANEL DE VENTAS 2019 - VERSIÓN FINAL".center(80))
print("="*80)
print("Desarrollado por: Paola Dueña - Data Analyst".center(80))
print("Versión: 50.1.0 - CON MEJORAS".center(80))
print("="*80)

# ============================================
# 1. CARGA DE DATOS REALES
# ============================================
print("\n📂 INICIALIZANDO DATA WAREHOUSE...")

ruta = r"C:\Users\USUARIO\Desktop\Ciencia de Datos\Dataset de ventas"
archivos = glob.glob(os.path.join(ruta, "Dataset_de_ventas_*.csv"))

if not archivos:
    print("\n" + "="*80)
    print("❌ ERROR CRÍTICO".center(80))
    print("="*80)
    print("\nNo se encontraron archivos CSV en la ruta:")
    print(f"   {ruta}")
    print("\nPor favor, verifica que:")
    print("   1. La ruta sea correcta")
    print("   2. Los archivos tengan el formato 'Dataset_de_ventas_*.csv'")
    print("   3. Los archivos existan en esa ubicación")
    print("\n" + "="*80)
    sys.exit(1)

print(f"   ✅ Archivos encontrados: {len(archivos)}")
df_list = []

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

if not df_list:
    print("\n❌ No se pudo cargar ningún archivo válido")
    sys.exit(1)

df = pd.concat(df_list, ignore_index=True)
print(f"\n   ✅ TOTAL: {len(df):,} registros procesados")

# ============================================
# 2. DATA WRANGLING
# ============================================
print("\n🔄 PROCESANDO DATOS...")

# Convertir columnas numéricas
df['Cantidad Pedida'] = pd.to_numeric(df['Cantidad Pedida'], errors='coerce')
df['Precio Unitario'] = pd.to_numeric(df['Precio Unitario'], errors='coerce')

# Eliminar filas con valores inválidos
df = df.dropna(subset=['Cantidad Pedida', 'Precio Unitario'])
df = df[(df['Cantidad Pedida'] > 0) & (df['Precio Unitario'] > 0)]

# Calcular ingresos
df['Ingreso Total'] = df['Cantidad Pedida'] * df['Precio Unitario']

# Procesar fechas
print("   • Procesando fechas...")
df['Fecha de Pedido'] = df['Fecha de Pedido'].astype(str)
df['Fecha Pedido'] = pd.to_datetime(df['Fecha de Pedido'], format='%m/%d/%y %H:%M', errors='coerce')

# Eliminar filas con fechas inválidas
df = df.dropna(subset=['Fecha Pedido'])

# Extraer componentes de fecha
df['Fecha'] = df['Fecha Pedido'].dt.date
df['Mes Num'] = df['Fecha Pedido'].dt.month
df['Día'] = df['Fecha Pedido'].dt.day
df['Hora'] = df['Fecha Pedido'].dt.hour
df['Día Semana'] = df['Fecha Pedido'].dt.dayofweek
df['Semana'] = df['Fecha Pedido'].dt.isocalendar().week
df['Día del Año'] = df['Fecha Pedido'].dt.dayofyear

# Mapas de meses
mapa_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}
df['Mes'] = df['Mes Num'].map(mapa_meses)

# Días en español
dias_espanol = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}
df['Día Semana Nombre'] = df['Fecha Pedido'].dt.day_name().map(dias_espanol)
df['Es Finde'] = df['Día Semana'].isin([5, 6])

# ============================================
# 3. EXTRACCIÓN DE UBICACIÓN
# ============================================
print("   • Procesando ubicaciones...")

def extraer_ubicacion(direccion):
    try:
        direccion = str(direccion)
        partes = direccion.split(',')
        if len(partes) >= 3:
            ciudad = partes[1].strip()
            estado_zip = partes[2].strip().split(' ')
            estado = estado_zip[0] if len(estado_zip) > 0 else 'Desconocido'
            return pd.Series([ciudad, estado])
    except:
        pass
    return pd.Series(['Desconocido', 'Desconocido'])

df[['Ciudad', 'Estado']] = df['Dirección de Envio'].apply(extraer_ubicacion)

# ============================================
# 4. CATEGORÍAS DE PRODUCTOS
# ============================================
print("   • Clasificando productos...")

def asignar_categoria(producto):
    producto = str(producto).lower()
    if 'batteries' in producto:
        return 'Baterías'
    elif 'cable' in producto:
        return 'Cables'
    elif any(x in producto for x in ['headphones', 'airpods', 'earpods', 'bose']):
        return 'Auriculares'
    elif any(x in producto for x in ['monitor', 'screen']):
        return 'Monitores'
    elif any(x in producto for x in ['laptop', 'macbook', 'thinkpad']):
        return 'Computadoras'
    elif any(x in producto for x in ['phone', 'iphone']):
        return 'Teléfonos'
    elif 'tv' in producto:
        return 'Televisores'
    elif any(x in producto for x in ['washing', 'dryer', 'lg']):
        return 'Electrodomésticos'
    else:
        return 'Otros'

df['Categoría'] = df['Producto'].apply(asignar_categoria)

# Rangos de precio
df['Rango Precio'] = pd.cut(df['Precio Unitario'], 
                            bins=[0, 20, 100, 500, 1000, 10000],
                            labels=['Económico', 'Medio', 'Premium', 'Alta Gama', 'Lujo'])

# ============================================
# 5. MAPA DE ESTADOS
# ============================================
print("   • Mapeando estados...")

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

# Códigos inversos para el mapa
codigos_estados = {v: k for k, v in estados_usa.items()}
codigos_estados['Desconocido'] = 'NA'

df['Estado Nombre'] = df['Estado'].map(estados_usa).fillna(df['Estado'])
df['Estado Codigo'] = df['Estado Nombre'].map(codigos_estados).fillna('NA')

# ============================================
# 6. EVENTOS ESPECIALES
# ============================================
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
    fecha_str = fecha.strftime('%Y-%m-%d')
    for evento, fechas in eventos.items():
        if fecha_str in fechas:
            return evento
    return 'Normal'

print("   • Identificando eventos en los datos...")
df['Evento'] = df['Fecha Pedido'].apply(identificar_evento)

# Ver qué eventos tienen datos
eventos_con_datos = []
for evento in eventos.keys():
    count = len(df[df['Evento'] == evento])
    if count > 0:
        eventos_con_datos.append(evento)
        print(f"      ✅ {evento}: {count:,.0f} registros")

print(f"   • Total eventos con datos: {len(eventos_con_datos)}")

# ============================================
# 7. KPIs GLOBALES
# ============================================
print("\n📊 CALCULANDO KPIs GLOBALES...")

TOTAL_INGRESOS = df['Ingreso Total'].sum()
TOTAL_PEDIDOS = df['ID de Pedido'].nunique()
TOTAL_UNIDADES = df['Cantidad Pedida'].sum()
TICKET_PROMEDIO = TOTAL_INGRESOS / TOTAL_PEDIDOS if TOTAL_PEDIDOS > 0 else 0
PRODUCTO_TOP = df.groupby('Producto')['Cantidad Pedida'].sum().idxmax() if not df.empty else "N/A"
CIUDAD_TOP = df.groupby('Ciudad')['Ingreso Total'].sum().idxmax() if not df.empty else "N/A"
ESTADO_TOP = df.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax() if not df.empty else "N/A"
HORA_PICO = df.groupby('Hora')['ID de Pedido'].nunique().idxmax() if not df.empty else 0
DIA_PICO = df.groupby('Día Semana Nombre')['ID de Pedido'].nunique().idxmax() if not df.empty else "N/A"

# Crecimiento anual
ventas_por_mes = df.groupby('Mes Num')['Ingreso Total'].sum()
if len(ventas_por_mes) > 1:
    CRECIMIENTO_ANUAL = ((ventas_por_mes.iloc[-1] - ventas_por_mes.iloc[0]) / ventas_por_mes.iloc[0] * 100)
else:
    CRECIMIENTO_ANUAL = 0

print(f"\n📊 RESUMEN DE DATOS:")
print(f"   • {len(df):,} registros válidos")
print(f"   • {df['Ciudad'].nunique()} ciudades | {df['Estado Nombre'].nunique()} estados")
print(f"   • Período: {df['Fecha'].min()} a {df['Fecha'].max()}")
print(f"   • Ingresos totales: ${TOTAL_INGRESOS:,.0f}")
print(f"   • Crecimiento: {CRECIMIENTO_ANUAL:+.1f}%")

# ============================================
# 8. FUNCIÓN PRODUCTO ESTRELLA
# ============================================
def analizar_producto_estrella(data, filtro_temporal):
    """
    Analiza el producto más vendido en un conjunto de datos filtrado.
    
    Parámetros:
        data (DataFrame): Datos filtrados
        filtro_temporal (str): Descripción del filtro aplicado
    
    Retorna:
        dict: Información detallada del producto estrella o None si no hay datos
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
        
        # Análisis de estacionalidad
        datos_producto = data[data['Producto'] == producto_top['Producto']]
        ventas_por_mes_prod = datos_producto.groupby('Mes')['Cantidad Pedida'].sum()
        mes_pico = ventas_por_mes_prod.idxmax() if not ventas_por_mes_prod.empty else "N/A"
        
        # Análisis de ubicación
        ciudades_top_prod = datos_producto.groupby('Ciudad')['Cantidad Pedida'].sum().nlargest(3).index.tolist()
        
        # Generar insights
        insights = []
        
        if share_producto > 20:
            insights.append(f"🔥 DOMINANTE: {share_producto:.1f}% de participación")
        elif share_producto > 10:
            insights.append(f"📊 SIGNIFICATIVO: {share_producto:.1f}% de participación")
        else:
            insights.append(f"📈 NICHO: {share_producto:.1f}% de participación")
        
        if comparacion_precio > 20:
            insights.append(f"💎 PREMIUM: ${producto_top['Precio Unitario']:.2f} ({comparacion_precio:+.1f}%)")
        elif comparacion_precio < -20:
            insights.append(f"💰 ECONÓMICO: ${producto_top['Precio Unitario']:.2f} ({comparacion_precio:+.1f}%)")
        else:
            insights.append(f"⚖️ COMPETITIVO: ${producto_top['Precio Unitario']:.2f}")
        
        if producto_top['Cantidad Pedida'] > 1000:
            insights.append(f"📦 ALTO VOLUMEN: {producto_top['Cantidad Pedida']:,.0f} unidades")
        elif producto_top['Cantidad Pedida'] > 500:
            insights.append(f"📦 VOLUMEN MEDIO: {producto_top['Cantidad Pedida']:,.0f} unidades")
        else:
            insights.append(f"📦 BAJO VOLUMEN: {producto_top['Cantidad Pedida']:,.0f} unidades")
        
        # Factores de éxito
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

# ============================================
# 9. FUNCIÓN PARA PRODUCTOS COMPLEMENTARIOS
# ============================================
def analizar_productos_complementarios(data):
    """
    Analiza qué productos se compran juntos con frecuencia.
    
    Parámetros:
        data (DataFrame): Datos de ventas
    
    Retorna:
        list: Top 5 pares de productos complementarios
    """
    if data.empty or len(data) < 100:
        return []
    
    try:
        pedidos = data.groupby('ID de Pedido')['Producto'].agg(list).reset_index()
        multi = pedidos[pedidos['Producto'].apply(len) > 1]
        
        if len(multi) == 0:
            return []
        
        pares = []
        for productos in multi['Producto']:
            if len(productos) > 1:
                productos_ordenados = sorted(set(productos))
                pares.extend(combinations(productos_ordenados, 2))
        
        top_pares = Counter(pares).most_common(5)
        return top_pares
    except:
        return []

# ============================================
# 10. FUNCIÓN PARA GENERAR INFORMES
# ============================================
def generar_informe_html(titulo, data, tablas=None):
    """Genera un informe HTML para exportar"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{titulo} - Panel de Ventas 2019</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            .kpi-card {{ display: inline-block; background: #f8f9fa; padding: 15px; margin: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .kpi-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .kpi-label {{ font-size: 14px; color: #7f8c8d; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #7f8c8d; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>{titulo}</h1>
        <p>Generado el: {timestamp}</p>
        <p>Período analizado: {data['Fecha'].min()} a {data['Fecha'].max()}</p>
        <p>Total de registros: {len(data):,}</p>
        
        <h2>KPIs Principales</h2>
        <div>
            <div class="kpi-card">
                <div class="kpi-label">Ingresos Totales</div>
                <div class="kpi-value">${data['Ingreso Total'].sum():,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Pedidos</div>
                <div class="kpi-value">{data['ID de Pedido'].nunique():,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Unidades Vendidas</div>
                <div class="kpi-value">{data['Cantidad Pedida'].sum():,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Ticket Promedio</div>
                <div class="kpi-value">${data['Ingreso Total'].sum() / data['ID de Pedido'].nunique():,.2f}</div>
            </div>
        </div>
    """
    
    if tablas:
        for titulo_tabla, df_tabla in tablas.items():
            if df_tabla is not None and not df_tabla.empty:
                html_content += f"<h2>{titulo_tabla}</h2>"
                html_content += df_tabla.to_html(index=False, classes="table table-striped")
    
    html_content += """
        <div class="footer">
            Informe generado automáticamente por el Panel de Ventas 2019<br>
            Desarrollado por Paola Dueña - Data Analyst
        </div>
    </body>
    </html>
    """
    
    return html_content

# ============================================
# 11. CONFIGURACIÓN DASHBOARD
# ============================================
print("\n🚀 Inicializando dashboard...")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Panel de Ventas 2019"

# Opciones para filtros
meses_list = ['Todos'] + list(mapa_meses.values())
estados_list = ['Todos'] + sorted(df['Estado Nombre'].unique())
ciudades_list = ['Todas'] + sorted(df['Ciudad'].unique())
categorias_list = ['Todas'] + sorted(df['Categoría'].unique())
rangos_list = ['Todos'] + ['Económico', 'Medio', 'Premium', 'Alta Gama', 'Lujo']
dias_list = ['Todos'] + ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

# MEJORA: Consistencia en filtros temporales - mismos valores que en el callback
filtros_temporales = [
    {'label': '🌐 General', 'value': 'General'},
    {'label': '📅 Por Mes', 'value': 'Mes'},
    {'label': '📆 Por Semana', 'value': 'Semana'},
    {'label': '📊 Por Día', 'value': 'Día'}
]

# ============================================
# 12. LAYOUT PRINCIPAL
# ============================================
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
    
    # Filtros Globales
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
                            dcc.Dropdown(id='ciudad', options=[{'label':'Todas','value':'Todas'}], value='Todas', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("📅 Mes", className="fw-bold"),
                            dcc.Dropdown(id='mes', options=[{'label':m,'value':m} for m in meses_list], value='Todos', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("📆 Día", className="fw-bold"),
                            dcc.Dropdown(id='dia', options=[{'label':d,'value':d} for d in dias_list], value='Todos', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("📦 Categoría", className="fw-bold"),
                            dcc.Dropdown(id='categoria', options=[{'label':c,'value':c} for c in categorias_list], value='Todas', clearable=False)
                        ], width=2),
                        dbc.Col([
                            html.Label("💰 Rango", className="fw-bold"),
                            dcc.Dropdown(id='rango', options=[{'label':r,'value':r} for r in rangos_list], value='Todos', clearable=False)
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
                                className="form-control"
                            )
                        ], width=9),
                        dbc.Col([
                            html.Label("🔄", className="fw-bold mt-3"),
                            html.Button("🔄 RESETEAR FILTROS", id='reset', className="btn btn-outline-danger w-100")
                        ], width=3),
                    ]),
                ])
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),
    
    # Pestañas
    dbc.Tabs([
        # ========================================
        # PESTAÑA 1: VISIÓN GENERAL
        # ========================================
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
            
            # MEJORA: Nuevo gráfico de variación mensual por estado
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("📊 Variación Mensual por Estado (Top 5)"), 
                    dbc.CardBody(dcc.Graph(id='graf-estados-mensual'))
                ], className="shadow-sm"), width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🎯 RESUMEN EJECUTIVO", className="bg-warning text-dark"), dbc.CardBody(id='resumen')]), width=12)
            ]),
            
            dcc.Download(id="download-general")
        ], label="📊 GENERAL"),
        
        # ========================================
        # PESTAÑA 2: COMPARADOR DE MESES
        # ========================================
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
                                        options=[{'label':m,'value':m} for m in meses_list if m!='Todos'],
                                        value=['Enero','Febrero','Marzo'],
                                        multi=True,
                                        placeholder="Selecciona meses..."
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Métrica a comparar:", className="fw-bold"),
                                    dcc.RadioItems(
                                        id='comp-metrica',
                                        options=[
                                            {'label':'💰 Ingresos','value':'ingresos'},
                                            {'label':'📦 Pedidos','value':'pedidos'}
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
                dbc.Col(dbc.Card([dbc.CardHeader("📈 Tendencia Comparativa"), dbc.CardBody(dcc.Graph(id='graf-comp-tend'))]), width=8),
                dbc.Col(dbc.Card([dbc.CardHeader("📊 Distribución por Hora"), dbc.CardBody(dcc.Graph(id='graf-comp-dist'))]), width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("📋 Tabla Comparativa Detallada"), dbc.CardBody(id='comp-tabla')]), width=12)
            ]),
            
            dcc.Download(id="download-comparador")
        ], label="📅 COMPARADOR"),
        
        # ========================================
        # PESTAÑA 3: PRODUCTO ESTRELLA
        # ========================================
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
                dbc.Col(dbc.Card([dbc.CardHeader("🏆 Producto por Mes"), dbc.CardBody(id='tabla-prod-mes')]), width=12)
            ]),
            
            dcc.Download(id="download-producto")
        ], label="🏆 PRODUCTO"),
        
        # ========================================
        # PESTAÑA 4: ANÁLISIS DE HORAS
        # ========================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("⏰ ANÁLISIS DE HORAS", className="bg-secondary text-white fw-bold"),
                        dbc.CardBody([
                            dcc.Tabs([
                                dcc.Tab(label="📊 Distribución por Hora", children=[
                                    dcc.Graph(id='graf-horas-dist'),
                                    html.P("👆 Haz clic en cualquier barra para ver los productos más vendidos en esa hora", 
                                           className="text-info text-center small mt-2")
                                ]),
                                dcc.Tab(label="🔥 Heatmap Hora vs Mes", children=[dcc.Graph(id='graf-horas-heat')]),
                                dcc.Tab(label="📈 Evolución Horas Pico", children=[dcc.Graph(id='graf-horas-evo')]),
                            ])
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🔥 Mapa de Calor"), dbc.CardBody(dcc.Graph(id='graf-heatmap'))]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("📆 Ventas por Día"), dbc.CardBody(dcc.Graph(id='graf-dias'))]), width=6)
            ]),
            
            dcc.Download(id="download-horas")
        ], label="⏰ HORAS"),
        
        # ========================================
        # PESTAÑA 5: EVENTOS ESPECIALES
        # ========================================
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
        
        # ========================================
        # PESTAÑA 6: PRODUCTOS COMPLEMENTARIOS
        # ========================================
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
            
            dcc.Download(id="download-complementos")
        ], label="🔄 COMPLEMENTOS"),
        
        # ========================================
        # PESTAÑA 7: PROPUESTAS ESTRATÉGICAS
        # ========================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📋 PROPUESTAS ESTRATÉGICAS 2020", className="bg-dark text-white fw-bold"),
                        dbc.CardBody(id='propuestas-content')
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-propuestas")
        ], label="📋 PROPUESTAS"),
        
    ], className="mb-4"),
    
    # Modales
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-horas-titulo")),
        dbc.ModalBody(id="modal-horas-contenido"),
        dbc.ModalFooter(dbc.Button("Cerrar", id="cerrar-modal-horas", className="ms-auto")),
    ], id="modal-horas", size="xl"),
    
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

# ============================================
# 13. CREAR BOTONES DE EVENTOS
# ============================================
botones_eventos = []
colores = ['primary', 'success', 'danger', 'warning', 'info', 'secondary']
for i, evento in enumerate(eventos_con_datos):
    color = colores[i % len(colores)]
    botones_eventos.append(
        dbc.Col(
            dbc.Button(
                evento,
                id=f'btn-evento-{i}',
                color=color,
                className="w-100 mb-2",
                n_clicks=0
            ),
            width=3
        )
    )

# ============================================
# 14. FUNCIÓN PARA GENERAR PROPUESTAS
# ============================================
def generar_propuestas():
    """Genera el contenido de la pestaña de propuestas estratégicas"""
    return html.Div([
        html.H4("🎯 RESUMEN EJECUTIVO", className="text-primary mt-4"),
        html.P("El análisis de ventas 2019 revela oportunidades significativas de crecimiento:", className="lead"),
        dbc.Table(
            html.Tbody([
                html.Tr([html.Td("📈 Crecimiento anual"), html.Td(f"+{CRECIMIENTO_ANUAL:.1f}%", className="text-success fw-bold"), html.Td("Excelente desempeño")]),
                html.Tr([html.Td("💰 Ticket promedio"), html.Td(f"${TICKET_PROMEDIO:,.2f}", className="text-info fw-bold"), html.Td("Oportunidad de upselling")]),
                html.Tr([html.Td("⏰ Hora pico"), html.Td(f"{HORA_PICO}:00", className="text-warning fw-bold"), html.Td("Alta actividad nocturna")]),
                html.Tr([html.Td("📆 Mejor día"), html.Td(f"{DIA_PICO}", className="text-danger fw-bold"), html.Td("Patrón atípico")]),
            ]),
            bordered=True, size="sm", className="mb-3"
        ),
        html.Hr(),
        
        # PROPUESTA 1
        dbc.Card([
            dbc.CardHeader([html.H5("📋 PROPUESTA 1: OPTIMIZACIÓN PUBLICITARIA"), dbc.Badge("ROI 300%", color="success", className="ms-2"), html.Span(" | Inversión: $50,000", className="ms-2 text-muted small")], className="bg-light"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("🔍 PROBLEMA", className="text-danger"),
                        html.P("Inversión publicitaria sin considerar patrones de compra."),
                        html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                        html.Ul([html.Li(f"⏰ Hora pico: {HORA_PICO}:00 (45% de las ventas)"), html.Li(f"📆 Mejor día: {DIA_PICO}")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li(f"📈 Aumentar ads: {DIA_PICO} 18-22h"), html.Li("⚡ Promociones relámpago: 19:00-20:00")]),
                        html.H6("📈 RESULTADOS ESPERADOS", className="text-info mt-3"),
                        html.P("💰 ROI 300%: Por cada $1 invertido, ganarás $3 netos."),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-primary border-4"),
        
        # PROPUESTA 2
        dbc.Card([
            dbc.CardHeader([html.H5("📦 PROPUESTA 2: VENTA CRUZADA"), dbc.Badge("ROI 500%", color="success", className="ms-2"), html.Span(" | Inversión: $20,000", className="ms-2 text-muted small")], className="bg-light"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("🔍 PROBLEMA", className="text-danger"),
                        html.P("Productos económicos tienen ticket bajo."),
                        html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                        html.Ul([html.Li("📱 iPhone + AirPods: +35% ticket")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li("💡 Sugerir complementarios en checkout")]),
                        html.H6("📈 RESULTADOS ESPERADOS", className="text-info mt-3"),
                        html.P("💰 ROI 500%: Por cada $1 invertido, ganarás $5 netos."),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-success border-4"),
        
        # PROPUESTA 3
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
                        html.Ul([html.Li("📅 Enero: Liquidación"), html.Li("🎁 Nov-Dic: Envío garantizado")]),
                        html.H6("📈 RESULTADOS ESPERADOS", className="text-info mt-3"),
                        html.P("💰 ROI 400%: Por cada $1 invertido, ganarás $4 netos."),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-warning border-4"),
    ])

# ============================================
# 15. CALLBACKS
# ============================================

@callback(
    [Output('ciudad', 'options'),
     Output('ciudad', 'value')],
    [Input('estado', 'value'),
     Input('reset', 'n_clicks')]
)
def update_ciudades(estado, reset):
    """Actualiza las opciones de ciudad según el estado seleccionado"""
    ctx = dash.callback_context
    if ctx.triggered and 'reset' in ctx.triggered[0]['prop_id']:
        return [{'label':'Todas','value':'Todas'}] + [{'label':c,'value':c} for c in sorted(df['Ciudad'].unique())], 'Todas'
    
    if estado == 'Todos':
        ciudades = ['Todas'] + sorted(df['Ciudad'].unique())
    else:
        ciudades = ['Todas'] + sorted(df[df['Estado Nombre']==estado]['Ciudad'].unique())
    return [{'label':c,'value':c} for c in ciudades], 'Todas'

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
    """Resetea todos los filtros a sus valores por defecto"""
    if not n_clicks:
        return [no_update] * 9
    return ('Todos','Todos','Todos','Todas','Todos', df['Fecha'].min(), df['Fecha'].max(), 'General', ['Enero','Febrero','Marzo'])

@callback(
    [Output('indicador-prod', 'children'),
     Output('titulo-factores', 'children')],
    Input('filtro-prod', 'value')
)
def update_titulos_prod(f):
    """Actualiza los títulos según el filtro de producto seleccionado"""
    if f == 'General':
        return "🌐 Análisis Global", "🔍 FACTORES DE ÉXITO"
    elif f == 'Mes':
        return "📅 Análisis por Mes", "🔍 FACTORES DE ÉXITO - POR MES"
    elif f == 'Semana':
        return "📆 Análisis por Semana", "🔍 FACTORES DE ÉXITO - POR SEMANA"
    else:
        return "📊 Análisis por Día", "🔍 FACTORES DE ÉXITO - POR DÍA"

@callback(
    Output('propuestas-content', 'children'),
    Input('propuestas-content', 'id')
)
def update_propuestas(_):
    """Actualiza el contenido de la pestaña de propuestas"""
    return generar_propuestas()

@callback(
    Output('botones-eventos', 'children'),
    Input('botones-eventos', 'id')
)
def mostrar_botones(_):
    """Muestra los botones de eventos"""
    return botones_eventos

# ========================================
# CALLBACK PRINCIPAL
# ========================================
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
     Output('graf-estados-mensual', 'figure'),  # MEJORA: Nuevo output
     Output('resumen', 'children'),
     Output('prod-container', 'children'),
     Output('tabla-prod-mes', 'children'),
     Output('factores-prod', 'children'),
     Output('graf-horas-dist', 'figure'),
     Output('graf-horas-heat', 'figure'),
     Output('graf-horas-evo', 'figure'),
     Output('graf-comp-tend', 'figure'),
     Output('graf-comp-dist', 'figure'),
     Output('comp-kpis', 'children'),
     Output('comp-tabla', 'children'),
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
    Callback principal que actualiza todos los gráficos y componentes del dashboard
    basándose en los filtros seleccionados.
    """
    
    # Aplicar filtros
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
    
    subtitulo = f"📊 {len(data):,} transacciones | {data['Ciudad'].nunique()} ciudades | {data['Producto'].nunique()} productos"
    
    # Figura vacía
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
                empty_fig, empty_fig, empty_fig, empty_resumen, empty_container, empty_table, empty_factores,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_table, empty_fig)
    
    # ========================================
    # KPIs
    # ========================================
    ingresos = data['Ingreso Total'].sum()
    pedidos = data['ID de Pedido'].nunique()
    unidades = data['Cantidad Pedida'].sum()
    ticket = ingresos / pedidos if pedidos > 0 else 0
    
    kpis = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("💰 INGRESOS"), html.H3(f"${ingresos:,.0f}")])], className="border-primary"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 PEDIDOS"), html.H3(f"{pedidos:,}")])], className="border-success"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🎫 TICKET"), html.H3(f"${ticket:,.2f}")])], className="border-info"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏙️ CIUDADES"), html.H3(f"{data['Ciudad'].nunique()}")])], className="border-warning"), width=3),
    ])
    
    # ========================================
    # Tendencias
    # ========================================
    ventas_mes = data.groupby('Mes Num')['Ingreso Total'].sum()
    crecimiento = 0
    if len(ventas_mes) > 1:
        crecimiento = ((ventas_mes.iloc[-1] - ventas_mes.iloc[0]) / ventas_mes.iloc[0] * 100)
    
    hora_pico = data.groupby('Hora')['ID de Pedido'].nunique().idxmax()
    dia_pico = data.groupby('Día Semana Nombre')['ID de Pedido'].nunique().idxmax()
    prod_top = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
    
    color_crec = "success" if crecimiento>0 else "danger" if crecimiento<0 else "warning"
    signo = "+" if crecimiento>0 else ""
    
    tendencias = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📈 CRECIMIENTO"), html.H3(f"{signo}{crecimiento:.1f}%", className=f"text-{color_crec}")])], className="bg-light"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("⏰ HORA PICO"), html.H3(f"{hora_pico}:00", className="text-warning")])], className="bg-light"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📆 MEJOR DÍA"), html.H3(dia_pico, className="text-info")])], className="bg-light"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏆 PRODUCTO"), html.H6(prod_top[:15], className="text-success")])], className="bg-light"), width=3),
    ])
    
    # ========================================
    # Gráfico 1: Ventas por Mes
    # ========================================
    df_mes = data.groupby('Mes')['Ingreso Total'].sum().reset_index()
    orden = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    df_mes['Mes'] = pd.Categorical(df_mes['Mes'], categories=orden, ordered=True)
    df_mes = df_mes.sort_values('Mes')
    
    fig_mes = px.bar(df_mes, x='Mes', y='Ingreso Total', title='💰 Ventas por Mes',
                    color='Ingreso Total', color_continuous_scale='Blues', text_auto='.2s')
    fig_mes.update_traces(texttemplate='$%{text:.2s}', textposition='outside')
    
    # ========================================
    # Gráfico 2: Tendencia Diaria
    # ========================================
    diario = data.groupby('Fecha')['Ingreso Total'].sum().reset_index()
    diario['Fecha'] = pd.to_datetime(diario['Fecha'])
    diario = diario.sort_values('Fecha')
    
    fig_tendencia = go.Figure()
    fig_tendencia.add_trace(go.Scatter(x=diario['Fecha'], y=diario['Ingreso Total'],
                                       mode='lines', line=dict(color='#8e44ad')))
    fig_tendencia.update_layout(title='📈 Tendencia Diaria')
    
    # ========================================
    # Gráfico 3: Heatmap
    # ========================================
    heat = data.groupby(['Hora','Día Semana Nombre']).size().reset_index(name='Pedidos')
    orden_dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    heat['Día Semana Nombre'] = pd.Categorical(heat['Día Semana Nombre'], categories=orden_dias, ordered=True)
    heat = heat.dropna().sort_values(['Día Semana Nombre','Hora'])
    
    fig_heatmap = px.density_heatmap(heat, x='Hora', y='Día Semana Nombre', z='Pedidos',
                                     title='🔥 Mapa de Calor - Horas Pico',
                                     color_continuous_scale='Viridis')
    
    # ========================================
    # Gráfico 4: Ventas por Día
    # ========================================
    dias = data.groupby(['Día Semana Nombre','Día Semana'])['ID de Pedido'].nunique().reset_index(name='Pedidos')
    dias = dias.sort_values('Día Semana')
    
    fig_dias = go.Figure()
    fig_dias.add_trace(go.Bar(x=dias['Día Semana Nombre'], y=dias['Pedidos'],
                              marker_color=['#3498db', '#3498db', '#3498db', '#3498db', '#3498db', '#e74c3c', '#e74c3c'],
                              text=dias['Pedidos'], textposition='outside'))
    fig_dias.update_layout(title='📆 Ventas por Día')
    
    # ========================================
    # Gráfico 5: Ciudades
    # ========================================
    top_ciud = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
    fig_ciudades = px.bar(top_ciud, x='Ingreso Total', y='Ciudad', orientation='h',
                          title='🏙️ Top 10 Ciudades', color='Ingreso Total',
                          color_continuous_scale='Reds', text_auto='.2s')
    fig_ciudades.update_traces(texttemplate='$%{text:.2s}')
    
    # ========================================
    # Gráfico 6: Mapa de Estados
    # ========================================
    ventas_estado = data.groupby('Estado Nombre')['Ingreso Total'].sum().reset_index()
    ventas_estado['codigo'] = ventas_estado['Estado Nombre'].map(codigos_estados)
    
    fig_mapa = go.Figure(data=go.Choropleth(
        locations=ventas_estado['codigo'],
        z=ventas_estado['Ingreso Total'],
        locationmode='USA-states',
        colorscale='Reds',
        colorbar_title="Ingresos ($)",
        text=ventas_estado['Estado Nombre']
    ))
    fig_mapa.update_layout(title='🗺️ Ventas por Estado', geo_scope='usa', height=400)
    
    # ========================================
    # MEJORA: Gráfico 7: Variación Mensual por Estado (Top 5)
    # ========================================
    # Calcular ventas por estado y mes
    ventas_estado_mes = data.groupby(['Estado Nombre', 'Mes'])['Ingreso Total'].sum().reset_index()
    
    # Obtener top 5 estados por ingreso total
    top_estados = data.groupby('Estado Nombre')['Ingreso Total'].sum().nlargest(5).index.tolist()
    
    # Filtrar para solo los top 5 estados
    ventas_top = ventas_estado_mes[ventas_estado_mes['Estado Nombre'].isin(top_estados)]
    
    # Crear gráfico de líneas para ver la evolución mensual
    fig_estados_mensual = go.Figure()
    
    colores_estados = px.colors.qualitative.Set2
    for i, estado_n in enumerate(top_estados):
        df_estado = ventas_top[ventas_top['Estado Nombre'] == estado_n]
        # Ordenar por mes
        df_estado['Mes'] = pd.Categorical(df_estado['Mes'], categories=orden, ordered=True)
        df_estado = df_estado.sort_values('Mes')
        
        fig_estados_mensual.add_trace(go.Scatter(
            x=df_estado['Mes'],
            y=df_estado['Ingreso Total'],
            mode='lines+markers',
            name=estado_n,
            line=dict(color=colores_estados[i % len(colores_estados)], width=3),
            marker=dict(size=8)
        ))
    
    fig_estados_mensual.update_layout(
        title='📊 Evolución Mensual de Ventas - Top 5 Estados',
        xaxis_title='Mes',
        yaxis_title='Ingresos ($)',
        hovermode='x unified',
        height=400
    )
    
    # ========================================
    # Resumen Ejecutivo
    # ========================================
    resumen = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏆 Producto"), html.P(prod_top[:20], className="text-success")])], className="border-success"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏙️ Ciudad"), html.P(data.groupby('Ciudad')['Ingreso Total'].sum().idxmax()[:20], className="text-primary")])], className="border-primary"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🗺️ Estado"), html.P(data.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax()[:20], className="text-info")])], className="border-info"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 Categoría"), html.P(data.groupby('Categoría')['Ingreso Total'].sum().idxmax()[:20], className="text-warning")])], className="border-warning"), width=3),
    ])
    
    # ========================================
    # Producto Estrella
    # ========================================
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
                html.H4(f"🏆 Producto Estrella: {analisis['producto'][:60]}", className="text-success"),
                html.P([
                    f"📦 {analisis['unidades']:,.0f} unidades | ",
                    f"💰 ${analisis['ingresos']:,.0f} | ",
                    f"📊 {analisis['share']:.1f}% participación"
                ]),
                html.P(f"📌 Basado en: {analisis['filtro_aplicado']}", className="small text-muted")
            ])
        ], className="bg-light border-2 border-success mb-3")
        
        factores = dbc.Card([
            dbc.CardHeader("🔍 Análisis detallado", className="bg-info text-white"),
            dbc.CardBody([
                html.H6("📊 Insights:", className="fw-bold"),
                html.Ul([html.Li(i) for i in analisis['insights']]),
                html.H6("📍 Factores de éxito:", className="fw-bold mt-3"),
                html.Ul([html.Li(i) for i in analisis['factores_exito']])
            ])
        ])
    else:
        prod_container = html.P("No hay datos suficientes")
        factores = html.P("No hay datos suficientes")
    
    # ========================================
    # Producto por Mes
    # ========================================
    prods_mes = data.groupby(['Mes','Producto'])['Cantidad Pedida'].sum().reset_index()
    idx = prods_mes.groupby('Mes')['Cantidad Pedida'].idxmax()
    top_mes = prods_mes.loc[idx].reset_index(drop=True)
    top_mes['Mes'] = pd.Categorical(top_mes['Mes'], categories=orden, ordered=True)
    top_mes = top_mes.sort_values('Mes')
    
    rows = []
    for _, r in top_mes.iterrows():
        rows.append(html.Tr([html.Td(r['Mes']), html.Td(r['Producto'][:30]), html.Td(f"{r['Cantidad Pedida']:,.0f}")]))
    
    tabla_prod_mes = dbc.Table(
        [html.Thead(html.Tr([html.Th("Mes"), html.Th("Producto"), html.Th("Cantidad")])),
         html.Tbody(rows)],
        striped=True, bordered=True, size='sm'
    )
    
    # ========================================
    # Gráficos de Horas
    # ========================================
    
    # Distribución por Hora
    horas = data.groupby('Hora')['ID de Pedido'].nunique().reset_index(name='Pedidos')
    fig_horas_dist = px.bar(horas, x='Hora', y='Pedidos', title='📊 Distribución por Hora',
                            color='Pedidos', color_continuous_scale='Viridis')
    
    # Heatmap Hora vs Mes
    heat_hm = data.groupby(['Mes','Hora']).size().reset_index(name='Pedidos')
    pivot = heat_hm.pivot(index='Mes', columns='Hora', values='Pedidos').fillna(0)
    pivot = pivot.reindex(orden)
    
    fig_horas_heat = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale='Viridis', hovertemplate='Mes: %{y}<br>Hora: %{x}<br>Pedidos: %{z}'
    ))
    fig_horas_heat.update_layout(title='🔥 Heatmap Hora vs Mes', height=400)
    
    # Evolución Horas Pico
    top_horas = horas.nlargest(5, 'Pedidos')['Hora'].tolist()
    horas_evo = data[data['Hora'].isin(top_horas)].groupby(['Mes','Hora']).size().reset_index(name='Pedidos')
    
    fig_horas_evo = go.Figure()
    colores_horas = px.colors.qualitative.Set1
    for i, hora in enumerate(sorted(top_horas)):
        dh = horas_evo[horas_evo['Hora'] == hora]
        if not dh.empty:
            fig_horas_evo.add_trace(go.Scatter(
                x=dh['Mes'], y=dh['Pedidos'],
                mode='lines+markers', name=f'{hora}:00',
                line=dict(color=colores_horas[i % len(colores_horas)], width=3)
            ))
    fig_horas_evo.update_layout(title='📈 Evolución Horas Pico')
    
    # ========================================
    # COMPARADOR
    # ========================================
    comp_kpis = html.P("Selecciona meses para comparar")
    fig_comp_tend = empty_fig
    fig_comp_dist = empty_fig
    comp_tabla = html.P("Selecciona meses")
    
    if meses_comp and len(meses_comp) > 0:
        meses_con_datos = [m for m in meses_comp if not data[data['Mes']==m].empty]
        if meses_con_datos:
            # KPIs
            filas = []
            for i in range(0, len(meses_con_datos), 3):
                fila = meses_con_datos[i:i+3]
                cols = []
                for m in fila:
                    dm = data[data['Mes']==m]
                    ingresos_m = dm['Ingreso Total'].sum()
                    pedidos_m = dm['ID de Pedido'].nunique()
                    
                    if metrica == 'ingresos':
                        valor = f"${ingresos_m:,.0f}"
                    else:
                        valor = f"{pedidos_m:,}"
                    
                    cols.append(dbc.Col(dbc.Card([
                        dbc.CardBody([html.H6(m), html.H4(valor, className="text-primary")])
                    ], className="border-primary"), width=4))
                filas.append(dbc.Row(cols, className="mb-2"))
            comp_kpis = html.Div(filas)
            
            # GRÁFICO TENDENCIA COMPARATIVA
            fig_comp_tend = go.Figure()
            colors = px.colors.qualitative.Set1
            for i, m in enumerate(meses_con_datos):
                dm = data[data['Mes']==m]
                dia = dm.groupby('Día')['Ingreso Total'].sum().reset_index()
                fig_comp_tend.add_trace(go.Scatter(
                    x=dia['Día'], 
                    y=dia['Ingreso Total'],
                    mode='lines+markers', 
                    name=m,
                    line=dict(color=colors[i % len(colors)], width=3)
                ))
            fig_comp_tend.update_layout(
                title='📈 Tendencia Comparativa por Mes',
                xaxis_title='Día del Mes',
                yaxis_title='Ingresos ($)',
                hovermode='x unified'
            )
            
            # MEJORA: GRÁFICO DE DISTRIBUCIÓN POR HORA PARA COMPARADOR
            fig_comp_dist = go.Figure()
            for i, m in enumerate(meses_con_datos):
                dm = data[data['Mes']==m]
                horas_m = dm.groupby('Hora')['ID de Pedido'].nunique().reset_index(name='Pedidos')
                fig_comp_dist.add_trace(go.Scatter(
                    x=horas_m['Hora'],
                    y=horas_m['Pedidos'],
                    mode='lines',
                    name=m,
                    line=dict(color=colors[i % len(colors)], width=2),
                    fill='tonexty' if i == 0 else None
                ))
            fig_comp_dist.update_layout(
                title='📊 Patrón Horario por Mes',
                xaxis_title='Hora del Día',
                yaxis_title='Pedidos',
                hovermode='x unified',
                height=300
            )
            
            # Tabla
            rows = []
            for m in meses_con_datos:
                dm = data[data['Mes']==m]
                rows.append(html.Tr([
                    html.Td(m),
                    html.Td(f"${dm['Ingreso Total'].sum():,.0f}"),
                    html.Td(f"{dm['ID de Pedido'].nunique():,}"),
                    html.Td(f"{dm['Cantidad Pedida'].sum():,}")
                ]))
            comp_tabla = dbc.Table(
                [html.Thead(html.Tr([html.Th("Mes"), html.Th("Ingresos"), html.Th("Pedidos"), html.Th("Unidades")])),
                 html.Tbody(rows)],
                striped=True, size='sm'
            )
    
    # ========================================
    # Productos Complementarios
    # ========================================
    top_pares = analizar_productos_complementarios(data)
    
    if top_pares:
        rows = []
        for i, ((a, b), c) in enumerate(top_pares, 1):
            rows.append(html.Tr([
                html.Td(f"#{i}"),
                html.Td(a[:25]),
                html.Td(b[:25]),
                html.Td(f"{c} veces", className="text-success")
            ]))
        
        prod_comp = dbc.Table(
            [html.Thead(html.Tr([html.Th("#"), html.Th("Producto A"), html.Th("Producto B"), html.Th("Frecuencia")])),
             html.Tbody(rows)],
            striped=True, size='sm'
        )
    else:
        prod_comp = html.P("No se encontraron pares significativos")
    
    return (subtitulo, kpis, tendencias, fig_mes, fig_tendencia, fig_heatmap, fig_dias,
            fig_ciudades, fig_mapa, fig_estados_mensual, resumen, prod_container, tabla_prod_mes, factores,
            fig_horas_dist, fig_horas_heat, fig_horas_evo,
            fig_comp_tend, fig_comp_dist, comp_kpis, comp_tabla, prod_comp)

# ========================================
# CALLBACK PARA MODAL DE HORAS (INTERACTIVO)
# ========================================
@callback(
    [Output('modal-horas', 'is_open'),
     Output('modal-horas-titulo', 'children'),
     Output('modal-horas-contenido', 'children')],
    [Input('graf-horas-dist', 'clickData'),
     Input('cerrar-modal-horas', 'n_clicks')],
    [State('modal-horas', 'is_open'),
     State('fechas', 'start_date'),
     State('fechas', 'end_date'),
     State('ciudad', 'value'),
     State('estado', 'value'),
     State('categoria', 'value'),
     State('mes', 'value'),
     State('dia', 'value')],
    prevent_initial_call=True
)
def modal_horas(clickData, cerrar_clicks, is_open, start, end, ciudad, estado, categoria, mes, dia):
    """
    Muestra un modal con detalles de productos cuando se hace clic en una hora del gráfico.
    """
    ctx = dash.callback_context
    
    # Si se cerró el modal
    if ctx.triggered and 'cerrar-modal-horas' in ctx.triggered[0]['prop_id']:
        return False, "", html.P("")
    
    if not clickData:
        return False, "", html.P("")
    
    # Obtener la hora clickeada
    hora = clickData['points'][0]['x']
    
    # Aplicar filtros
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
    
    try:
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        data = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    except:
        pass
    
    # Filtrar por la hora seleccionada
    data_hora = data[data['Hora'] == hora]
    
    if data_hora.empty:
        return True, f"⏰ Hora: {hora}:00", html.P("No hay datos para esta hora")
    
    # Top 10 productos
    top_productos = data_hora.groupby('Producto').agg({
        'Cantidad Pedida': 'sum',
        'Ingreso Total': 'sum',
        'ID de Pedido': 'nunique'
    }).sort_values('Cantidad Pedida', ascending=False).head(10).reset_index()
    
    rows = []
    for _, r in top_productos.iterrows():
        ticket_promedio = r['Ingreso Total'] / r['ID de Pedido'] if r['ID de Pedido'] > 0 else 0
        rows.append(html.Tr([
            html.Td(r['Producto'][:40]),
            html.Td(f"{r['Cantidad Pedida']:,.0f}", className="text-end"),
            html.Td(f"${r['Ingreso Total']:,.0f}", className="text-end"),
            html.Td(f"{r['ID de Pedido']:,}", className="text-end"),
            html.Td(f"${ticket_promedio:,.2f}", className="text-end")
        ]))
    
    tabla = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Producto"),
            html.Th("Unidades", className="text-end"),
            html.Th("Ingresos", className="text-end"),
            html.Th("Pedidos", className="text-end"),
            html.Th("Ticket Prom", className="text-end")
        ])),
         html.Tbody(rows)],
        striped=True, bordered=True, hover=True, size='sm'
    )
    
    # KPIs de la hora
    total_unidades = data_hora['Cantidad Pedida'].sum()
    total_ingresos = data_hora['Ingreso Total'].sum()
    total_pedidos = data_hora['ID de Pedido'].nunique()
    ticket_promedio_hora = total_ingresos / total_pedidos if total_pedidos > 0 else 0
    
    # Comparación con el promedio general
    promedio_general_unidades = data['Cantidad Pedida'].sum() / 24 if len(data) > 0 else 0
    variacion = ((total_unidades / promedio_general_unidades) - 1) * 100 if promedio_general_unidades > 0 else 0
    
    contenido = html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📦 Unidades", className="text-center"),
                    html.H4(f"{total_unidades:,.0f}", className="text-center text-primary")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Ingresos", className="text-center"),
                    html.H4(f"${total_ingresos:,.0f}", className="text-center text-success")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📋 Pedidos", className="text-center"),
                    html.H4(f"{total_pedidos:,}", className="text-center text-info")
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🎫 Ticket", className="text-center"),
                    html.H4(f"${ticket_promedio_hora:,.2f}", className="text-center text-warning")
                ])
            ]), width=3),
        ], className="mb-3"),
        html.P(f"📊 Esta hora representa el {variacion:+.1f}% del promedio por hora", 
               className="text-muted small text-end"),
        html.Hr(),
        html.H5(f"📦 Top 10 productos más vendidos a las {hora}:00"),
        tabla
    ])
    
    return True, f"⏰ Hora: {hora}:00", contenido

# ========================================
# CALLBACK PARA EVENTOS
# ========================================
@callback(
    Output("resultado-eventos", "children"),
    [Input(f'btn-evento-{i}', 'n_clicks') for i in range(len(eventos_con_datos))],
    prevent_initial_call=True
)
def mostrar_evento(*args):
    """
    Muestra el análisis detallado de un evento especial cuando se hace clic en su botón.
    """
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return html.P("Haz clic en un botón para ver los detalles del evento")
    
    # Identificar qué botón se clickeó
    boton_id = ctx.triggered[0]['prop_id'].split('.')[0]
    indice = int(boton_id.replace('btn-evento-', ''))
    evento_nombre = eventos_con_datos[indice]
    
    # Filtrar datos del evento
    data_evento = df[df['Evento'] == evento_nombre]
    
    if data_evento.empty:
        return html.Div([
            dbc.Alert(f"No hay datos para {evento_nombre}", color="warning")
        ])
    
    # Calcular métricas
    total_ingresos = data_evento['Ingreso Total'].sum()
    total_pedidos = data_evento['ID de Pedido'].nunique()
    total_unidades = data_evento['Cantidad Pedida'].sum()
    ticket_promedio = total_ingresos / total_pedidos if total_pedidos > 0 else 0
    
    # Top 5 productos
    top_productos = data_evento.groupby('Producto')['Cantidad Pedida'].sum().nlargest(5).reset_index()
    top_productos.columns = ['Producto', 'Unidades Vendidas']
    
    # Calcular comparación con día normal
    data_normal = df[df['Evento'] == 'Normal']
    if not data_normal.empty:
        ventas_por_dia_normal = data_normal.groupby('Fecha')['Ingreso Total'].sum().mean()
        incremento = ((total_ingresos / ventas_por_dia_normal) - 1) * 100 if ventas_por_dia_normal > 0 else 0
    else:
        incremento = 0
    
    # Determinar color según incremento
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
    
    # Crear resultado
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
                ], className="mb-4"),
                
                html.H5("🏆 Top 5 Productos Más Vendidos", className="mb-3"),
                dbc.Table.from_dataframe(top_productos, striped=True, bordered=True, hover=True),
            ])
        ])
    ])
    
    return resultado

# ============================================
# 16. EJECUCIÓN
# ============================================
def abrir_navegador():
    """Abre el navegador automáticamente después de iniciar el servidor"""
    webbrowser.open('http://127.0.0.1:8050')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("✅ DASHBOARD INICIADO".center(80))
    print("="*80)
    print("\n🌐 http://127.0.0.1:8050")
    print(f"\n📊 {len(df):,} registros | ${TOTAL_INGRESOS:,.0f} | {TOTAL_PEDIDOS:,} pedidos")
    print(f"\n🎉 Eventos con datos ({len(eventos_con_datos)}):")
    for e in eventos_con_datos:
        print(f"   • {e}: {len(df[df['Evento'] == e]):,} registros")
    print("\n✅ Pestañas: GENERAL | COMPARADOR | PRODUCTO | HORAS | EVENTOS | COMPLEMENTOS | PROPUESTAS")
    print("\n✅ MEJORAS IMPLEMENTADAS:")
    print("   • Gráfico de variación mensual por estado (Top 5)")
    print("   • Gráfico de distribución por hora en comparador")
    print("   • Consistencia en filtros temporales")
    print("   • Documentación mejorada con docstrings")
    print("\n" + "="*80)
    
    threading.Timer(2, abrir_navegador).start()
    app.run(debug=False, port=8050)