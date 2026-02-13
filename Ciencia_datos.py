#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
                         PANEL DE VENTAS 2019
================================================================================
Desarrollado por: Paola Dueña - Data Analyst
Empresa: Análisis de Ventas 2019
Versión: 2.0.0 - Enterprise Edition
================================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output, no_update, callback
import dash_bootstrap_components as dbc
import glob
import os
import webbrowser
import threading
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("PANEL DE VENTAS 2019".center(80))
print("="*80)
print("Desarrollado por: Paola Dueña - Data Analyst".center(80))
print("Versión: 2.0.0 - Enterprise Edition".center(80))
print("="*80)

# ============================================
# 1. CARGA DE DATOS
# ============================================
print("\n📂 INICIALIZANDO DATA WAREHOUSE...")

ruta = r"C:\Users\USUARIO\Desktop\Ciencia de Datos\Dataset de ventas"
archivos = glob.glob(os.path.join(ruta, "Dataset_de_ventas_*.csv"))

if not archivos:
    print(f"\n❌ ERROR: No se encontraron archivos CSV en {ruta}")
    exit()

df_list = []
for archivo in archivos:
    nombre = os.path.basename(archivo)
    mes = nombre.replace('Dataset_de_ventas_', '').replace('.csv', '')
    df_temp = pd.read_csv(archivo)
    df_temp = df_temp[df_temp['ID de Pedido'] != 'Order ID']
    df_temp = df_temp.dropna(subset=['ID de Pedido'])
    df_temp['Mes'] = mes
    df_list.append(df_temp)

df = pd.concat(df_list, ignore_index=True)
print(f"   ✅ {len(df):,} registros procesados")

# ============================================
# 2. DATA WRANGLING & FEATURE ENGINEERING
# ============================================
print("\n🔄 DATA WRANGLING & FEATURE ENGINEERING...")

# Convertir tipos
df['Cantidad Pedida'] = pd.to_numeric(df['Cantidad Pedida'], errors='coerce')
df['Precio Unitario'] = pd.to_numeric(df['Precio Unitario'], errors='coerce')
df = df.dropna(subset=['Cantidad Pedida', 'Precio Unitario'])
df = df[(df['Cantidad Pedida'] > 0) & (df['Precio Unitario'] > 0)]

# Calcular ingresos
df['Ingreso Total'] = df['Cantidad Pedida'] * df['Precio Unitario']

# Feature Engineering - Fechas
df['Fecha Pedido'] = pd.to_datetime(df['Fecha de Pedido'], format='%m/%d/%y %H:%M', errors='coerce')
df = df.dropna(subset=['Fecha Pedido'])
df['Fecha'] = df['Fecha Pedido'].dt.date
df['Año'] = df['Fecha Pedido'].dt.year
df['Mes Num'] = df['Fecha Pedido'].dt.month
df['Día'] = df['Fecha Pedido'].dt.day
df['Hora'] = df['Fecha Pedido'].dt.hour
df['Minuto'] = df['Fecha Pedido'].dt.minute
df['Día Semana'] = df['Fecha Pedido'].dt.dayofweek
df['Nombre Día'] = df['Fecha Pedido'].dt.day_name()
df['Semana'] = df['Fecha Pedido'].dt.isocalendar().week
df['Trimestre'] = df['Fecha Pedido'].dt.quarter
df['Año-Mes'] = df['Fecha Pedido'].dt.to_period('M').astype(str)
df['Día del Año'] = df['Fecha Pedido'].dt.dayofyear

# Mapear meses a español
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
df['Día'] = df['Nombre Día'].map(dias_espanol)
df['Es Finde'] = df['Día Semana'].isin([5, 6])

# Feature Engineering - Ubicación
def extraer_ubicacion(direccion):
    try:
        partes = str(direccion).split(',')
        if len(partes) >= 3:
            ciudad = partes[1].strip()
            estado_zip = partes[2].strip().split(' ')
            estado = estado_zip[0] if len(estado_zip) > 0 else 'Desconocido'
            return pd.Series([ciudad, estado])
        return pd.Series(['Desconocido', 'Desconocido'])
    except:
        return pd.Series(['Desconocido', 'Desconocido'])

df[['Ciudad', 'Estado']] = df['Dirección de Envio'].apply(extraer_ubicacion)

# Feature Engineering - Categorías de productos
def asignar_categoria(producto):
    producto = str(producto).lower()
    if 'batteries' in producto:
        return 'Baterías'
    elif 'cable' in producto:
        return 'Cables'
    elif 'headphones' in producto or 'airpods' in producto or 'earpods' in producto or 'bose' in producto:
        return 'Auriculares'
    elif 'monitor' in producto or 'screen' in producto:
        return 'Monitores'
    elif 'laptop' in producto or 'macbook' in producto or 'thinkpad' in producto:
        return 'Computadoras'
    elif 'phone' in producto or 'iphone' in producto:
        return 'Teléfonos'
    elif 'tv' in producto or 'television' in producto:
        return 'Televisores'
    elif 'washing' in producto or 'dryer' in producto or 'lg' in producto:
        return 'Electrodomésticos'
    else:
        return 'Otros'

df['Categoría'] = df['Producto'].apply(asignar_categoria)

# Feature Engineering - Rangos de precio
df['Rango Precio'] = pd.cut(df['Precio Unitario'], 
                            bins=[0, 20, 100, 500, 1000, 10000],
                            labels=['Económico', 'Medio', 'Premium', 'Alta Gama', 'Lujo'])

# ============================================
# 3. MAPA DE NOMBRES COMPLETOS DE ESTADOS
# ============================================
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

df['Estado Nombre'] = df['Estado'].map(estados_usa).fillna(df['Estado'])

print(f"   ✅ {df['Ciudad'].nunique()} ciudades | {df['Estado Nombre'].nunique()} estados")
print(f"   ✅ Período: {df['Fecha'].min()} a {df['Fecha'].max()}")

# ============================================
# 4. KPI's - MÉTRICAS CLAVE
# ============================================
print("\n📊 CALCULANDO KPIs...")

# Métricas globales
TOTAL_INGRESOS = df['Ingreso Total'].sum()
TOTAL_PEDIDOS = df['ID de Pedido'].nunique()
TOTAL_UNIDADES = df['Cantidad Pedida'].sum()
TICKET_PROMEDIO = TOTAL_INGRESOS / TOTAL_PEDIDOS
PRODUCTO_TOP = df.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
CIUDAD_TOP = df.groupby('Ciudad')['Ingreso Total'].sum().idxmax()
ESTADO_TOP = df.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax()
HORA_PICO = df.groupby('Hora')['ID de Pedido'].nunique().idxmax()
DIA_PICO = df.groupby('Día')['ID de Pedido'].nunique().idxmax()

# Métricas de crecimiento
ventas_por_mes = df.groupby('Mes Num')['Ingreso Total'].sum()
if len(ventas_por_mes) > 1:
    CRECIMIENTO_ANUAL = ((ventas_por_mes.iloc[-1] - ventas_por_mes.iloc[0]) / ventas_por_mes.iloc[0] * 100)
else:
    CRECIMIENTO_ANUAL = 0

print(f"   ✅ Ingresos totales: ${TOTAL_INGRESOS:,.0f}")
print(f"   ✅ Crecimiento: {CRECIMIENTO_ANUAL:+.1f}%")

# ============================================
# 4.5 DEFINICIÓN DE EVENTOS ESPECIALES
# ============================================
eventos_especiales = {
    'Año Nuevo': ['2019-01-01', '2020-01-01'],
    'San Valentín': ['2019-02-14'],
    'Día de San Patricio': ['2019-03-17'],
    'Pascua': ['2019-04-21'],
    'Día de la Madre': ['2019-05-12'],
    'Día del Padre': ['2019-06-16'],
    'Independencia de EE.UU.': ['2019-07-04'],
    'Back to School': ['2019-08-15', '2019-08-16', '2019-08-17', '2019-08-18', '2019-08-19'],
    'Labor Day': ['2019-09-02'],
    'Halloween': ['2019-10-31'],
    'Veterans Day': ['2019-11-11'],
    'Black Friday': ['2019-11-29'],
    'Cyber Monday': ['2019-12-02'],
    'Navidad': ['2019-12-24', '2019-12-25'],
    'Año Nuevo 2020': ['2020-01-01']
}

# Función para identificar eventos
def identificar_evento(fecha):
    fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
    for evento, fechas in eventos_especiales.items():
        if fecha_str in fechas:
            return evento
    return 'Día Normal'

# ============================================
# 5. INICIAR DASHBOARD
# ============================================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Panel de Ventas 2019"

# Opciones para filtros
estados_opciones = ['Todos'] + sorted(df['Estado Nombre'].unique())
meses_opciones = ['Todos'] + list(mapa_meses.values())
dias_opciones = ['Todos'] + ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
categorias_opciones = ['Todas'] + sorted(df['Categoría'].unique())
rangos_precio = ['Todos'] + ['Económico', 'Medio', 'Premium', 'Alta Gama', 'Lujo']

# ============================================
# 6. LAYOUT PROFESIONAL
# ============================================
app.layout = dbc.Container([
    
    # HEADER
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H2("Panel de Ventas 2019", 
                       className="text-center text-white fw-light mb-2"),
                html.H6(id='subtitulo', className="text-center text-white mt-1 small"),
                html.Hr(className="bg-white opacity-25 my-2"),
                html.P(f"Data Warehouse: {len(df):,} registros | Período: {df['Fecha'].min()} a {df['Fecha'].max()}",
                      className="text-center text-white-50 small mb-0"),
            ], className="p-3")
        ], className="bg-gradient bg-primary rounded-lg shadow-sm")
    ], className="mb-4"),
    
    # FILTROS - PRIMERA FILA
    dbc.Row([
        dbc.Col([
            html.Label("📍 Estado", className="fw-bold text-muted"),
            dcc.Dropdown(id='estado', 
                        options=[{'label': e, 'value': e} for e in estados_opciones],
                        value='Todos', clearable=False, className="mb-2")
        ], width=3),
        
        dbc.Col([
            html.Label("🏙️ Ciudad", className="fw-bold text-muted"),
            dcc.Dropdown(id='ciudad', value='Todas', clearable=False, className="mb-2")
        ], width=3),
        
        dbc.Col([
            html.Label("📅 Mes", className="fw-bold text-muted"),
            dcc.Dropdown(id='mes', 
                        options=[{'label': m, 'value': m} for m in meses_opciones],
                        value='Todos', clearable=False, className="mb-2")
        ], width=3),
        
        dbc.Col([
            html.Label("📆 Día de Semana", className="fw-bold text-muted"),
            dcc.Dropdown(id='dia', 
                        options=[{'label': d, 'value': d} for d in dias_opciones],
                        value='Todos', clearable=False, className="mb-2")
        ], width=3),
    ], className="mb-3"),
    
    # FILTROS - SEGUNDA FILA
    dbc.Row([
        dbc.Col([
            html.Label("📊 Trimestre", className="fw-bold text-muted"),
            dcc.Dropdown(id='trimestre', options=[
                {'label': 'Todos', 'value': 'Todos'},
                {'label': 'Q1 - Ene-Mar', 'value': 1},
                {'label': 'Q2 - Abr-Jun', 'value': 2},
                {'label': 'Q3 - Jul-Sep', 'value': 3},
                {'label': 'Q4 - Oct-Dic', 'value': 4}
            ], value='Todos', clearable=False, className="mb-2")
        ], width=3),
        
        dbc.Col([
            html.Label("📦 Categoría", className="fw-bold text-muted"),
            dcc.Dropdown(id='categoria', 
                        options=[{'label': c, 'value': c} for c in categorias_opciones],
                        value='Todas', clearable=False, className="mb-2")
        ], width=3),
        
        dbc.Col([
            html.Label("💰 Rango de Precio", className="fw-bold text-muted"),
            dcc.Dropdown(id='rango_precio', 
                        options=[{'label': r, 'value': r} for r in rangos_precio],
                        value='Todos', clearable=False, className="mb-2")
        ], width=3),
        
        dbc.Col([
            html.Label("📅 Rango de Fechas", className="fw-bold text-muted"),
            dcc.DatePickerRange(
                id='fechas',
                start_date=df['Fecha'].min(),
                end_date=df['Fecha'].max(),
                display_format='DD/MM/YYYY',
                className="form-control"
            )
        ], width=3),
    ], className="mb-4"),
    
    # BOTÓN RESET
    dbc.Row([
        dbc.Col([
            html.Button([
                "🔄 RESETEAR FILTROS"
            ], id='reset', className="btn btn-outline-danger btn-lg w-100 shadow-sm"),
        ], width=12),
    ], className="mb-4"),
    
    # KPIs
    dbc.Row(id='kpis', className="mb-4"),
    
    # ANÁLISIS DE TENDENCIAS
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("📈 ANÁLISIS DE TENDENCIAS", 
                           className="mb-0 text-white"),
                ], className="bg-gradient bg-info"),
                dbc.CardBody(id='tendencias')
            ], className="shadow-sm")
        ], width=12),
    ], className="mb-4"),
    
    # GRÁFICOS - FILA 1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("💰 Ventas por Mes"),
                dbc.CardBody(dcc.Graph(id='graf-ventas-mes'))
            ], className="shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Tendencia Diaria"),
                dbc.CardBody(dcc.Graph(id='graf-tendencia'))
            ], className="shadow-sm")
        ], width=6),
    ], className="mb-4"),
    
    # GRÁFICOS - FILA 2
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔥 Mapa de Calor - Horas Pico"),
                dbc.CardBody(dcc.Graph(id='graf-heatmap'))
            ], className="shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📆 Ventas por Día"),
                dbc.CardBody(dcc.Graph(id='graf-dias'))
            ], className="shadow-sm")
        ], width=6),
    ], className="mb-4"),
    
    # GRÁFICOS - FILA 3
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📦 Top 10 Productos"),
                dbc.CardBody(dcc.Graph(id='graf-productos'))
            ], className="shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🏙️ Top 10 Ciudades"),
                dbc.CardBody(dcc.Graph(id='graf-ciudades'))
            ], className="shadow-sm")
        ], width=6),
    ], className="mb-4"),
    
    # TABLA COMPARATIVA
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 ANÁLISIS COMPARATIVO POR MES", 
                              className="bg-success text-white"),
                dbc.CardBody(id='tabla-meses', style={'overflowX': 'auto'})
            ], className="shadow-sm")
        ], width=12),
    ], className="mb-4"),
    
    # RESUMEN EJECUTIVO
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎯 RESUMEN EJECUTIVO", 
                              className="bg-warning"),
                dbc.CardBody(id='resumen')
            ], className="shadow-sm")
        ], width=12),
    ]),
    
    # NUEVA SECCIÓN: EVENTOS ESPECIALES
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎉 ANÁLISIS DE EVENTOS ESPECIALES", 
                              className="bg-danger text-white"),
                dbc.CardBody(id='eventos-especiales')
            ], className="shadow-sm")
        ], width=12),
    ], className="mb-4"),
    
    # FOOTER CON ENLACES
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.Div([
                html.Span("📊 Desarrollado por: Paola Dueña - Data Analyst | ", 
                         className="text-muted small"),
                html.A(" LinkedIn", 
                      href="https://ar.linkedin.com/in/paoladit", 
                      target="_blank",
                      className="text-primary small text-decoration-none"),
                html.Span(" | ", className="text-muted small"),
                html.A(" paoladf.it@gmail.com", 
                      href="mailto:paoladf.it@gmail.com",
                      className="text-primary small text-decoration-none"),
                html.Br(),
                html.Span(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                         className="text-muted small"),
            ], className="text-center")
        ], width=12),
    ], className="mt-4"),
    
], fluid=True)

# ============================================
# 7. CALLBACKS
# ============================================

@callback(
    [Output('ciudad', 'options'),
     Output('ciudad', 'value')],
    [Input('estado', 'value'),
     Input('reset', 'n_clicks')]
)
def update_ciudades(estado, reset):
    if estado == 'Todos':
        ciudades = ['Todas'] + sorted(df['Ciudad'].unique())
    else:
        ciudades_filtradas = sorted(df[df['Estado Nombre'] == estado]['Ciudad'].unique())
        ciudades = ['Todas'] + ciudades_filtradas
    return [{'label': c, 'value': c} for c in ciudades], 'Todas'

@callback(
    [Output('estado', 'value'),
     Output('mes', 'value'),
     Output('dia', 'value'),
     Output('trimestre', 'value'),
     Output('categoria', 'value'),
     Output('rango_precio', 'value'),
     Output('fechas', 'start_date'),
     Output('fechas', 'end_date')],
    [Input('reset', 'n_clicks')]
)
def reset_filtros(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return [no_update] * 8
    return ('Todos', 'Todos', 'Todos', 'Todos', 'Todas', 'Todos',
            df['Fecha'].min(), df['Fecha'].max())

@callback(
    [Output('kpis', 'children'),
     Output('subtitulo', 'children'),
     Output('tendencias', 'children'),
     Output('graf-ventas-mes', 'figure'),
     Output('graf-tendencia', 'figure'),
     Output('graf-heatmap', 'figure'),
     Output('graf-dias', 'figure'),
     Output('graf-productos', 'figure'),
     Output('graf-ciudades', 'figure'),
     Output('tabla-meses', 'children'),
     Output('resumen', 'children'),
     Output('eventos-especiales', 'children')],
    [Input('ciudad', 'value'),
     Input('estado', 'value'),
     Input('mes', 'value'),
     Input('dia', 'value'),
     Input('trimestre', 'value'),
     Input('categoria', 'value'),
     Input('rango_precio', 'value'),
     Input('fechas', 'start_date'),
     Input('fechas', 'end_date'),
     Input('reset', 'n_clicks')]
)
def update_dashboard(ciudad, estado, mes, dia, trimestre, categoria, rango_precio, start, end, reset):
    
    # Aplicar filtros
    data = df.copy()
    
    if estado != 'Todos':
        data = data[data['Estado Nombre'] == estado]
    if ciudad != 'Todas':
        data = data[data['Ciudad'] == ciudad]
    if mes != 'Todos':
        data = data[data['Mes'] == mes]
    if dia != 'Todos':
        data = data[data['Día'] == dia]
    if trimestre != 'Todos':
        data = data[data['Trimestre'] == trimestre]
    if categoria != 'Todas':
        data = data[data['Categoría'] == categoria]
    if rango_precio != 'Todos':
        data = data[data['Rango Precio'] == rango_precio]
    
    data = data[(data['Fecha'] >= pd.to_datetime(start).date()) & 
                (data['Fecha'] <= pd.to_datetime(end).date())]
    
    # Subtítulo
    subtitulo = f"📊 Mostrando: {len(data):,} transacciones | {data['Ciudad'].nunique()} ciudades activas"
    
    # ========================================
    # KPIs
    # ========================================
    ingresos = data['Ingreso Total'].sum()
    pedidos = data['ID de Pedido'].nunique()
    unidades = data['Cantidad Pedida'].sum()
    ticket = ingresos / pedidos if pedidos > 0 else 0
    ciudades_activas = data['Ciudad'].nunique()
    categorias_activas = data['Categoría'].nunique()
    
    kpis = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("💰 INGRESOS TOTALES", className="text-muted"),
                html.H3(f"${ingresos:,.0f}", className="text-primary fw-bold"),
                html.P(f"{((ingresos/TOTAL_INGRESOS)*100):.1f}% del total", className="small text-muted"),
            ])
        ], className="border-start border-primary border-4 shadow-sm"), width=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("📦 PEDIDOS", className="text-muted"),
                html.H3(f"{pedidos:,}", className="text-success fw-bold"),
                html.P(f"{unidades:,} unidades", className="small text-muted"),
            ])
        ], className="border-start border-success border-4 shadow-sm"), width=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("🎫 TICKET PROMEDIO", className="text-muted"),
                html.H3(f"${ticket:,.2f}", className="text-info fw-bold"),
                html.P(f"{categorias_activas} categorías", className="small text-muted"),
            ])
        ], className="border-start border-info border-4 shadow-sm"), width=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("🏙️ CIUDADES ACTIVAS", className="text-muted"),
                html.H3(f"{ciudades_activas}", className="text-warning fw-bold"),
                html.P(f"{data['Estado'].nunique()} estados", className="small text-muted"),
            ])
        ], className="border-start border-warning border-4 shadow-sm"), width=3),
    ])
    
    # ========================================
    # ANÁLISIS DE TENDENCIAS
    # ========================================
    if not data.empty:
        # Calcular crecimiento
        ventas_por_mes_filt = data.groupby('Mes')['Ingreso Total'].sum().reset_index()
        if len(ventas_por_mes_filt) > 1:
            primer_valor = ventas_por_mes_filt['Ingreso Total'].iloc[0]
            ultimo_valor = ventas_por_mes_filt['Ingreso Total'].iloc[-1]
            crecimiento = ((ultimo_valor - primer_valor) / primer_valor * 100) if primer_valor > 0 else 0
        else:
            crecimiento = 0
        
        # Métricas clave
        hora_pico_actual = data.groupby('Hora')['ID de Pedido'].nunique().idxmax()
        dia_pico_actual = data.groupby('Día')['ID de Pedido'].nunique().idxmax()
        producto_top_actual = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
        ciudad_top_actual = data.groupby('Ciudad')['Ingreso Total'].sum().idxmax()
        
        tendencias = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📈 CRECIMIENTO", className="text-center"),
                    html.H3(f"{crecimiento:+.1f}%", 
                           className=f"text-center text-{'success' if crecimiento>0 else 'danger'}"),
                ])
            ], className="bg-light"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("⏰ HORA PICO", className="text-center"),
                    html.H3(f"{hora_pico_actual}:00", className="text-center text-warning"),
                ])
            ], className="bg-light"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📆 MEJOR DÍA", className="text-center"),
                    html.H3(dia_pico_actual, className="text-center text-info"),
                ])
            ], className="bg-light"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🏆 PRODUCTO TOP", className="text-center"),
                    html.H6(producto_top_actual[:25] + ('...' if len(producto_top_actual) > 25 else ''), 
                           className="text-center text-success", style={'fontSize': '14px'}),
                ])
            ], className="bg-light"), width=3),
        ])
    else:
        tendencias = html.P("Datos insuficientes para análisis de tendencias", className="text-center text-muted")
    
    # ========================================
    # GRÁFICOS
    # ========================================
    
    # Gráfico 1: Ventas por Mes
    if not data.empty:
        df_mes = data.groupby('Mes')['Ingreso Total'].sum().reset_index()
        fig1 = px.bar(df_mes, x='Mes', y='Ingreso Total', 
                     title='💰 Ventas por Mes',
                     color='Ingreso Total', color_continuous_scale='Blues',
                     text_auto='.2s')
        fig1.update_traces(texttemplate='$%{text:.2s}', textposition='outside')
        fig1.update_layout(height=350, showlegend=False, 
                          yaxis_title="Ingresos ($)", xaxis_title="Mes")
    else:
        fig1 = px.bar(title="Sin datos disponibles")
    
    # Gráfico 2: Tendencia Diaria
    if not data.empty:
        diario = data.groupby('Fecha')['Ingreso Total'].sum().reset_index()
        diario['Fecha'] = pd.to_datetime(diario['Fecha'])
        diario = diario.sort_values('Fecha')
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=diario['Fecha'], y=diario['Ingreso Total'],
                                  mode='lines+markers', name='Ventas diarias',
                                  line=dict(color='#8e44ad', width=2)))
        if len(diario) > 7:
            diario['MA7'] = diario['Ingreso Total'].rolling(7).mean()
            fig2.add_trace(go.Scatter(x=diario['Fecha'], y=diario['MA7'],
                                      name='Promedio 7 días', 
                                      line=dict(color='red', width=2, dash='dot')))
        fig2.update_layout(title='📈 Tendencia de Ventas Diarias', height=350,
                          yaxis_title="Ingresos ($)", xaxis_title="Fecha")
    else:
        fig2 = go.Figure()
    
    # Gráfico 3: Heatmap
    if not data.empty:
        heat = data.groupby(['Hora', 'Día']).size().reset_index(name='Pedidos')
        orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        heat['Día'] = pd.Categorical(heat['Día'], categories=orden, ordered=True)
        heat = heat.sort_values(['Día', 'Hora'])
        fig3 = px.density_heatmap(heat, x='Hora', y='Día', z='Pedidos', 
                                 title='🔥 Mapa de Calor - Horas Pico',
                                 color_continuous_scale='Viridis')
        fig3.update_layout(height=350, yaxis_title="Día", xaxis_title="Hora")
    else:
        fig3 = px.density_heatmap(title="Sin datos disponibles")
    
    # Gráfico 4: Ventas por Día
    if not data.empty:
        dias = data.groupby(['Día', 'Día Semana'])['ID de Pedido'].nunique().reset_index(name='Pedidos')
        dias = dias.sort_values('Día Semana')
        colors = ['#3498db']*5 + ['#e74c3c']*2
        fig4 = px.bar(dias, x='Día', y='Pedidos', 
                     title='📆 Ventas por Día de la Semana',
                     color='Día', color_discrete_sequence=colors, 
                     text_auto=True)
        fig4.update_traces(texttemplate='%{y:,}', textposition='outside')
        fig4.update_layout(height=350, showlegend=False, yaxis_title="Pedidos")
    else:
        fig4 = px.bar(title="Sin datos disponibles")
    
    # Gráfico 5: Top Productos
    if not data.empty:
        top_prod = data.groupby('Producto')['Cantidad Pedida'].sum().nlargest(10).reset_index()
        fig5 = px.bar(top_prod, x='Cantidad Pedida', y='Producto', 
                     title='📦 Top 10 Productos más Vendidos',
                     orientation='h', color='Cantidad Pedida', 
                     color_continuous_scale='Greens', text_auto=True)
        fig5.update_layout(height=350, yaxis_title="", xaxis_title="Unidades Vendidas")
    else:
        fig5 = px.bar(title="Sin datos disponibles")
    
    # Gráfico 6: Top Ciudades
    if not data.empty:
        top_ciud = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
        fig6 = px.bar(top_ciud, x='Ingreso Total', y='Ciudad', 
                     title='🏙️ Top 10 Ciudades por Ingresos',
                     orientation='h', color='Ingreso Total', 
                     color_continuous_scale='Reds', text_auto='.2s')
        fig6.update_traces(texttemplate='$%{text:.2s}')
        fig6.update_layout(height=350, yaxis_title="", xaxis_title="Ingresos ($)")
    else:
        fig6 = px.bar(title="Sin datos disponibles")
    
    # ========================================
    # TABLA COMPARATIVA
    # ========================================
    if not data.empty:
        tabla_df = data.groupby('Mes').agg({
            'Ingreso Total': 'sum',
            'ID de Pedido': 'nunique',
            'Cantidad Pedida': 'sum'
        }).reset_index()
        
        # Calcular variaciones
        tabla_df['Variación %'] = tabla_df['Ingreso Total'].pct_change() * 100
        tabla_df['Variación %'] = tabla_df['Variación %'].fillna(0).round(1)
        
        tabla_df['Ingreso Total'] = tabla_df['Ingreso Total'].apply(lambda x: f'${x:,.0f}')
        tabla_df['ID de Pedido'] = tabla_df['ID de Pedido'].apply(lambda x: f'{x:,}')
        tabla_df['Cantidad Pedida'] = tabla_df['Cantidad Pedida'].apply(lambda x: f'{x:,}')
        tabla_df['Variación %'] = tabla_df['Variación %'].apply(lambda x: f'{x:+.1f}%')
        tabla_df.columns = ['Mes', 'Ingresos', 'Pedidos', 'Unidades', 'Variación']
        
        tabla_meses = dbc.Table.from_dataframe(
            tabla_df, striped=True, bordered=True, hover=True, size='sm'
        )
    else:
        tabla_meses = html.P("Sin datos para la tabla comparativa", className="text-center text-muted")
    
    # ========================================
    # RESUMEN EJECUTIVO
    # ========================================
    if len(data) > 0:
        prod_top = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
        ciudad_top = data.groupby('Ciudad')['Ingreso Total'].sum().idxmax()
        estado_top = data.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax()
        cat_top = data.groupby('Categoría')['Ingreso Total'].sum().idxmax()
        
        resumen = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🏆 Producto Estrella", className="text-center"),
                    html.P(prod_top, className="text-center text-success fw-bold"),
                ])
            ], className="h-100 shadow-sm border-success"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🏙️ Ciudad Top", className="text-center"),
                    html.P(ciudad_top, className="text-center text-primary fw-bold"),
                ])
            ], className="h-100 shadow-sm border-primary"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🗺️ Estado Top", className="text-center"),
                    html.P(estado_top, className="text-center text-info fw-bold"),
                ])
            ], className="h-100 shadow-sm border-info"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📦 Categoría Top", className="text-center"),
                    html.P(cat_top, className="text-center text-warning fw-bold"),
                ])
            ], className="h-100 shadow-sm border-warning"), width=3),
        ])
    else:
        resumen = html.P("Datos insuficientes para resumen ejecutivo", className="text-center text-muted")
    
    # ========================================
    # ANÁLISIS DE EVENTOS ESPECIALES
    # ========================================
    if len(data) > 0:
        # Crear columna de eventos
        data_con_eventos = data.copy()
        data_con_eventos['Evento'] = data_con_eventos['Fecha Pedido'].apply(identificar_evento)
        
        # Análisis por evento
        ventas_por_evento = data_con_eventos.groupby('Evento').agg({
            'Ingreso Total': ['sum', 'mean'],
            'ID de Pedido': 'nunique',
            'Cantidad Pedida': 'sum'
        }).round(0)
        
        ventas_por_evento.columns = ['Ingresos Totales', 'Ticket Promedio', 'Pedidos', 'Unidades']
        ventas_por_evento = ventas_por_evento.reset_index()
        ventas_por_evento = ventas_por_evento[ventas_por_evento['Evento'] != 'Día Normal']
        
        if not ventas_por_evento.empty:
            # Calcular promedio diario normal para comparación
            ventas_normales = data_con_eventos[data_con_eventos['Evento'] == 'Día Normal']['Ingreso Total'].mean()
            
            # Crear tarjetas para cada evento
            tarjetas_eventos = []
            for _, row in ventas_por_evento.iterrows():
                variacion = ((row['Ingresos Totales'] / ventas_normales) - 1) * 100 if ventas_normales > 0 else 0
                color = "success" if variacion > 0 else "danger" if variacion < 0 else "warning"
                
                tarjetas_eventos.append(
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6(row['Evento'], className="text-center fw-bold"),
                            html.H4(f"${row['Ingresos Totales']:,.0f}", 
                                   className=f"text-center text-{color}"),
                            html.P(f"{variacion:+.1f}% vs día normal", 
                                  className="text-center small"),
                            html.P(f"{row['Pedidos']:,.0f} pedidos", 
                                  className="text-center small text-muted"),
                        ])
                    ], className=f"border-{color} border-2 shadow-sm"), width=3)
                )
            
            # Gráfico de comparación de eventos
            fig_eventos = px.bar(ventas_por_evento.sort_values('Ingresos Totales', ascending=False),
                                x='Evento', y='Ingresos Totales',
                                title='💰 Ingresos en Días Especiales',
                                color='Ingresos Totales',
                                color_continuous_scale='RdYlGn',
                                text_auto='.2s')
            fig_eventos.update_traces(texttemplate='$%{text:.2s}')
            fig_eventos.update_layout(height=350, xaxis_tickangle=-45)
            
            eventos_content = dbc.Container([
                dbc.Row(tarjetas_eventos, className="mb-3"),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_eventos), width=12)
                ])
            ])
        else:
            eventos_content = html.P("No hay días especiales en el período seleccionado", 
                                    className="text-center text-muted")
    else:
        eventos_content = html.P("Datos insuficientes para análisis de eventos", 
                                className="text-center text-muted")
    
    return kpis, subtitulo, tendencias, fig1, fig2, fig3, fig4, fig5, fig6, tabla_meses, resumen, eventos_content

# ============================================
# 8. EJECUTAR DASHBOARD
# ============================================
def abrir_navegador():
    webbrowser.open('http://127.0.0.1:8050')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("✅ PANEL DE VENTAS 2019 INICIADO".center(80))
    print("="*80)
    print("\n🌐 Accede a tu dashboard:")
    print("   🔗 http://127.0.0.1:8050")
    print("\n📊 Métricas principales:")
    print(f"   • Ingresos Totales: ${TOTAL_INGRESOS:,.0f}")
    print(f"   • Pedidos Totales: {TOTAL_PEDIDOS:,}")
    print(f"   • Ticket Promedio: ${TICKET_PROMEDIO:,.2f}")
    print(f"   • Crecimiento: {CRECIMIENTO_ANUAL:+.1f}%")
    print("\n" + "="*80)
    print("⏳ Presiona CTRL+C para detener el servidor")
    print("="*80 + "\n")
    
    threading.Timer(2, abrir_navegador).start()
    app.run(debug=False, port=8050)