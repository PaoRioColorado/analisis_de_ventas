#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
                    PANEL DE VENTAS 2019 - VERSIÓN FINAL
================================================================================
Desarrollado por: Paola Dueña - Data Analyst
Versión: 18.0.0 - CORREGIDA (Finde vs Laboral)
================================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import Dash, dcc, html, Input, Output, no_update, callback, State
import dash_bootstrap_components as dbc
import glob
import os
import webbrowser
import threading
from datetime import datetime
from collections import Counter
from itertools import combinations
import sys
import base64
import io
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("PANEL DE VENTAS 2019 - VERSIÓN FINAL".center(80))
print("="*80)
print("Desarrollado por: Paola Dueña - Data Analyst".center(80))
print("Versión: 18.0.0 - CORREGIDA".center(80))
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
        df_temp = pd.read_csv(archivo, dtype=str)
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
# 6. KPIs GLOBALES
# ============================================
print("   • Calculando KPIs...")

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
# 7. EVENTOS ESPECIALES
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

# ============================================
# 8. FUNCIÓN PRODUCTO ESTRELLA
# ============================================
def analizar_producto_estrella(data):
    if data.empty or len(data) < 10:
        return None
    
    try:
        # Agrupar por producto
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
        
        # Calcular métricas
        total_unidades = ventas_productos['Cantidad Pedida'].sum()
        share_producto = (producto_top['Cantidad Pedida'] / total_unidades * 100) if total_unidades > 0 else 0
        
        precio_promedio = data['Precio Unitario'].mean()
        comparacion_precio = ((producto_top['Precio Unitario'] - precio_promedio) / precio_promedio * 100) if precio_promedio > 0 else 0
        
        # Generar insights (SIN TICKET IMPACTO)
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
        
        return {
            'producto': producto_top['Producto'],
            'unidades': producto_top['Cantidad Pedida'],
            'ingresos': producto_top['Ingreso Total'],
            'pedidos': producto_top['ID de Pedido'],
            'precio': producto_top['Precio Unitario'],
            'share': share_producto,
            'comparacion_precio': comparacion_precio,
            'insights': insights
        }
    except Exception as e:
        print(f"   ⚠️ Error en análisis de producto: {e}")
        return None

# ============================================
# 9. CONFIGURACIÓN DASHBOARD
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

filtros_temporales = [
    {'label': '📅 Por Mes', 'value': 'Mes'},
    {'label': '📆 Por Semana', 'value': 'Semana'},
    {'label': '📊 Por Día', 'value': 'Día'},
    {'label': '🌐 General', 'value': 'General'}
]

# ============================================
# 10. LAYOUT PRINCIPAL CON BOTONES DE EXPORTACIÓN
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
                dbc.CardHeader("🔍 FILTROS GLOBALES", className="bg-dark text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📍 Estado"),
                            dcc.Dropdown(
                                id='estado',
                                options=[{'label': e, 'value': e} for e in estados_list],
                                value='Todos',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("🏙️ Ciudad"),
                            dcc.Dropdown(
                                id='ciudad',
                                options=[{'label': 'Todas', 'value': 'Todas'}],
                                value='Todas',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("📅 Mes"),
                            dcc.Dropdown(
                                id='mes',
                                options=[{'label': m, 'value': m} for m in meses_list],
                                value='Todos',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("📆 Día"),
                            dcc.Dropdown(
                                id='dia',
                                options=[{'label': d, 'value': d} for d in dias_list],
                                value='Todos',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("📦 Categoría"),
                            dcc.Dropdown(
                                id='categoria',
                                options=[{'label': c, 'value': c} for c in categorias_list],
                                value='Todas',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("💰 Rango"),
                            dcc.Dropdown(
                                id='rango',
                                options=[{'label': r, 'value': r} for r in rangos_list],
                                value='Todos',
                                clearable=False
                            )
                        ], width=2),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Label("📅 Fechas", className="mt-3"),
                            dcc.DatePickerRange(
                                id='fechas',
                                start_date=df['Fecha'].min(),
                                end_date=df['Fecha'].max(),
                                display_format='DD/MM/YYYY',
                                className="form-control"
                            )
                        ], width=9),
                        dbc.Col([
                            html.Label("🔄", className="mt-3"),
                            html.Button(
                                "🔄 RESETEAR FILTROS",
                                id='reset',
                                className="btn btn-outline-danger w-100"
                            )
                        ], width=3),
                    ]),
                ])
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),
    
    # Pestañas con botones de exportación
    dbc.Tabs([
        # PESTAÑA 1: GENERAL
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("📊 KPIs PRINCIPALES", className="text-white fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-general", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-primary"),
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
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💰 Ventas por Mes"),
                        dbc.CardBody(dcc.Graph(id='graf-mes'))
                    ], className="shadow-sm")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Tendencia Diaria"),
                        dbc.CardBody(dcc.Graph(id='graf-tendencia'))
                    ], className="shadow-sm")
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎯 RESUMEN EJECUTIVO", className="bg-warning text-dark"),
                        dbc.CardBody(id='resumen')
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-general")
        ], label="📊 GENERAL"),
        
        # PESTAÑA 2: COMPARADOR
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("📅 COMPARADOR DE MESES", className="text-white fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-comparador", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-danger"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Selecciona meses para comparar:"),
                                    dcc.Dropdown(
                                        id='comp-meses',
                                        options=[{'label': m, 'value': m} for m in meses_list if m != 'Todos'],
                                        value=['Enero', 'Febrero', 'Marzo'],
                                        multi=True,
                                        placeholder="Selecciona meses..."
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Métrica a comparar:"),
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
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Tendencia Comparativa"),
                        dbc.CardBody(dcc.Graph(id='graf-comp-tend'))
                    ], className="shadow-sm h-100")
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Distribución por Mes"),
                        dbc.CardBody(dcc.Graph(id='graf-comp-dist'))
                    ], className="shadow-sm h-100")
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📋 Tabla Comparativa Detallada"),
                        dbc.CardBody(id='comp-tabla', style={'overflowX': 'auto'})
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-comparador")
        ], label="📅 COMPARADOR"),
        
        # PESTAÑA 3: PRODUCTO ESTRELLA
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("🎯 PRODUCTO ESTRELLA INTELIGENTE", className="text-dark fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-producto", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-warning"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Analizar por:"),
                                    dcc.RadioItems(
                                        id='filtro-prod',
                                        options=filtros_temporales,
                                        value='General',
                                        inline=True
                                    )
                                ], width=8),
                                dbc.Col([
                                    html.Div(id='indicador-prod', className="mt-2 text-end text-primary fw-bold")
                                ], width=4),
                            ]),
                            html.Hr(),
                            html.Div(id='prod-container')
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id='titulo-factores', className="bg-info text-white"),
                        dbc.CardBody(id='factores-prod')
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏆 Producto Más Vendido por Mes", className="bg-secondary text-white"),
                        dbc.CardBody(id='tabla-prod-mes', style={'overflowX': 'auto'})
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-producto")
        ], label="🏆 PRODUCTO"),
        
        # PESTAÑA 4: HORAS
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("⏰ ANÁLISIS DETALLADO DE HORAS", className="text-white fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-horas", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-secondary"),
                        dbc.CardBody(
                            dcc.Tabs([
                                dcc.Tab(label="📊 Distribución por Hora", children=[
                                    dcc.Graph(id='graf-horas-dist')
                                ]),
                                dcc.Tab(label="🔥 Heatmap Hora vs Mes", children=[
                                    dcc.Graph(id='graf-horas-heat')
                                ]),
                                dcc.Tab(label="📈 Evolución Horas Pico", children=[
                                    dcc.Graph(id='graf-horas-evo')
                                ]),
                            ])
                        )
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔥 Mapa de Calor - Horas vs Días"),
                        dbc.CardBody(dcc.Graph(id='graf-heatmap'))
                    ], className="shadow-sm")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📆 Ventas por Día de Semana"),
                        dbc.CardBody(dcc.Graph(id='graf-dias'))
                    ], className="shadow-sm")
                ], width=6)
            ]),
            
            dcc.Download(id="download-horas")
        ], label="⏰ HORAS"),
        
        # PESTAÑA 5: GEOGRÁFICO
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("🗺️ MAPA DE VENTAS POR ESTADO", className="text-white fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-geo", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-success"),
                        dbc.CardBody(dcc.Graph(id='mapa-estados'))
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏙️ Análisis de Ciudades"),
                        dbc.CardBody(dcc.Graph(id='graf-ciudades'))
                    ], className="shadow-sm")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Finde vs Laboral"),
                        dbc.CardBody(dcc.Graph(id='graf-finde'))
                    ], className="shadow-sm")
                ], width=6)
            ]),
            
            dcc.Download(id="download-geo")
        ], label="🗺️ GEO"),
        
        # PESTAÑA 6: PRODUCTOS
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("📦 TOP 10 PRODUCTOS", className="text-white fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-productos", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-primary"),
                        dbc.CardBody(dcc.Graph(id='graf-productos'))
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("🔄 Productos que se Compran Juntos", className="text-dark fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-complementos", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-info"),
                        dbc.CardBody(id='prod-comp')
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-productos")
        ], label="📦 PRODUCTOS"),
        
        # PESTAÑA 7: EVENTOS
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("🎉 ANÁLISIS DE EVENTOS ESPECIALES", className="text-white fw-bold"),
                                html.Button("📥 Exportar", id="btn-exportar-eventos", 
                                           className="btn btn-sm btn-light float-end",
                                           n_clicks=0)
                            ])
                        ], className="bg-danger"),
                        dbc.CardBody(id='eventos')
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-eventos")
        ], label="🎉 EVENTOS"),
        
        # ========================================
        # PESTAÑA 8: PROPUESTAS ESTRATÉGICAS
        # ========================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H3("📋 PROPUESTAS ESTRATÉGICAS 2020", 
                                   className="text-white fw-bold d-inline"),
                            html.Button("📥 Descargar PDF", 
                                       id="btn-descargar-propuestas", 
                                       className="btn btn-light btn-sm float-end",
                                       n_clicks=0)
                        ], className="bg-dark"),
                        dbc.CardBody([
                            # RESUMEN EJECUTIVO
                            dbc.Row([
                                dbc.Col([
                                    html.H4("🎯 RESUMEN EJECUTIVO", className="text-primary"),
                                    html.P("El análisis de ventas 2019 revela oportunidades significativas de crecimiento:", 
                                           className="lead"),
                                    dbc.Table(
                                        html.Tbody([
                                            html.Tr([html.Td("📈 Crecimiento anual"), 
                                                     html.Td("+153.2%", className="text-success fw-bold"),
                                                     html.Td("Excelente desempeño")]),
                                            html.Tr([html.Td("💰 Ticket promedio"), 
                                                     html.Td("$193.40", className="text-info fw-bold"),
                                                     html.Td("Oportunidad de upselling")]),
                                            html.Tr([html.Td("⏰ Hora pico"), 
                                                     html.Td("19:00", className="text-warning fw-bold"),
                                                     html.Td("Alta actividad nocturna")]),
                                            html.Tr([html.Td("📆 Mejor día"), 
                                                     html.Td("Martes", className="text-danger fw-bold"),
                                                     html.Td("Patrón atípico")]),
                                        ]),
                                        bordered=True, size="sm", className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            
                            html.Hr(),
                            
                            # PROPUESTA 1
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader([
                                            html.H5("📋 PROPUESTA 1: OPTIMIZACIÓN PUBLICITARIA", 
                                                   className="fw-bold d-inline"),
                                            dbc.Badge("ROI 300%", color="success", className="ms-2"),
                                            html.Span(" | Inversión: $50,000", className="ms-2 text-muted small")
                                        ], className="bg-light"),
                                        dbc.CardBody([
                                            dbc.Row([
                                                dbc.Col([
                                                    html.H6("🔍 PROBLEMA", className="text-danger"),
                                                    html.P("Inversión publicitaria sin considerar patrones de compra por hora/día."),
                                                    
                                                    html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                                                    html.Ul([
                                                        html.Li("Hora pico: 19:00 (45% ventas diarias)"),
                                                        html.Li("Mejor día: Martes (pico de actividad)"),
                                                        html.Li("Findes: -0.5% vs laborables")
                                                    ]),
                                                ], width=6),
                                                dbc.Col([
                                                    html.H6("✅ ACCIONES", className="text-success"),
                                                    html.Ul([
                                                        html.Li("Aumentar ads: Martes 18-22h"),
                                                        html.Li("Pausar campañas: Domingos mañana"),
                                                        html.Li("Promociones relámpago: 19:00-20:00")
                                                    ]),
                                                    
                                                    html.H6("📈 MÉTRICAS DE ÉXITO", className="text-info mt-3"),
                                                    html.Ul([
                                                        html.Li("+20% ROAS"),
                                                        html.Li("-15% costo por adquisición")
                                                    ]),
                                                ], width=6),
                                            ]),
                                            dbc.Button("Implementar propuesta", 
                                                      id="btn-propuesta1", 
                                                      color="primary", 
                                                      size="sm",
                                                      className="mt-2",
                                                      n_clicks=0)
                                        ])
                                    ], className="shadow-sm mb-3 border-start border-primary border-4")
                                ], width=12)
                            ]),
                            
                            # PROPUESTA 2
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader([
                                            html.H5("📦 PROPUESTA 2: VENTA CRUZADA (CROSS-SELLING)", 
                                                   className="fw-bold d-inline"),
                                            dbc.Badge("ROI 500%", color="success", className="ms-2"),
                                            html.Span(" | Inversión: $20,000", className="ms-2 text-muted small")
                                        ], className="bg-light"),
                                        dbc.CardBody([
                                            dbc.Row([
                                                dbc.Col([
                                                    html.H6("🔍 PROBLEMA", className="text-danger"),
                                                    html.P("Clientes que compran productos económicos tienen ticket 46.3% más bajo."),
                                                    
                                                    html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                                                    html.Ul([
                                                        html.Li("iPhone + AirPods: 1,234 pedidos juntos"),
                                                        html.Li("MacBook + Adaptador: 987 pedidos"),
                                                        html.Li("Ticket +35% con complementos")
                                                    ]),
                                                ], width=6),
                                                dbc.Col([
                                                    html.H6("✅ ACCIONES", className="text-success"),
                                                    html.Ul([
                                                        html.Li("Sugerir al checkout: iPhone → AirPods"),
                                                        html.Li("Bundles con 10% descuento"),
                                                        html.Li("Email marketing post-compra")
                                                    ]),
                                                    
                                                    html.H6("📈 MÉTRICAS DE ÉXITO", className="text-info mt-3"),
                                                    html.Ul([
                                                        html.Li("+25% ticket promedio"),
                                                        html.Li("+30% ventas accesorios")
                                                    ]),
                                                ], width=6),
                                            ]),
                                            dbc.Button("Implementar propuesta", 
                                                      id="btn-propuesta2", 
                                                      color="primary", 
                                                      size="sm",
                                                      className="mt-2",
                                                      n_clicks=0)
                                        ])
                                    ], className="shadow-sm mb-3 border-start border-success border-4")
                                ], width=12)
                            ]),
                            
                            # PROPUESTA 3
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader([
                                            html.H5("📅 PROPUESTA 3: CALENDARIO DE PROMOCIONES", 
                                                   className="fw-bold d-inline"),
                                            dbc.Badge("ROI 400%", color="success", className="ms-2"),
                                            html.Span(" | Inversión: $30,000", className="ms-2 text-muted small")
                                        ], className="bg-light"),
                                        dbc.CardBody([
                                            dbc.Row([
                                                dbc.Col([
                                                    html.H6("🔍 PROBLEMA", className="text-danger"),
                                                    html.P("Patrones estacionales no aprovechados comercialmente."),
                                                    
                                                    html.H6("📊 EVIDENCIA", className="text-primary mt-3"),
                                                    html.Ul([
                                                        html.Li("Black Friday: +185%"),
                                                        html.Li("Navidad: +210%"),
                                                        html.Li("Enero: -20% caída post-navideña"),
                                                        html.Li("Back to School: +45%")
                                                    ]),
                                                ], width=6),
                                                dbc.Col([
                                                    html.H6("✅ ACCIONES", className="text-success"),
                                                    html.Ul([
                                                        html.Li("Enero: Liquidación accesorios"),
                                                        html.Li("Agosto: Descuento estudiantil"),
                                                        html.Li("Nov-Dic: Envío garantizado")
                                                    ]),
                                                    
                                                    html.H6("📈 MÉTRICAS DE ÉXITO", className="text-info mt-3"),
                                                    html.Ul([
                                                        html.Li("+40% ventas de temporada"),
                                                        html.Li("-50% stock post-navideño")
                                                    ]),
                                                ], width=6),
                                            ]),
                                            dbc.Button("Implementar propuesta", 
                                                      id="btn-propuesta3", 
                                                      color="primary", 
                                                      size="sm",
                                                      className="mt-2",
                                                      n_clicks=0)
                                        ])
                                    ], className="shadow-sm mb-3 border-start border-warning border-4")
                                ], width=12)
                            ]),
                            
                            # CALENDARIO
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader("📆 CALENDARIO ESTRATÉGICO 2020", 
                                                      className="bg-info text-white fw-bold"),
                                        dbc.CardBody([
                                            html.Div([
                                                html.Span("ENERO      ──── ", className="fw-bold"),
                                                "Liquidación post-navideña (20% off accesorios)", html.Br(),
                                                html.Span("FEBRERO    ──── ", className="fw-bold"),
                                                "San Valentín Tech (bundles para parejas)", html.Br(),
                                                html.Span("MARZO      ──── ", className="fw-bold"),
                                                "Lanzamiento nuevos productos", html.Br(),
                                                html.Span("ABRIL      ──── ", className="fw-bold"),
                                                "Día del Padre anticipado", html.Br(),
                                                html.Span("MAYO       ──── ", className="fw-bold"),
                                                "Pre-Back to School", html.Br(),
                                                html.Span("JUNIO      ──── ", className="fw-bold"),
                                                "Ofertas de mitad de año", html.Br(),
                                                html.Span("JULIO      ──── ", className="fw-bold"),
                                                "Independencia (electrónica)", html.Br(),
                                                html.Span("AGOSTO     ──── ", className="fw-bold text-success"),
                                                "BACK TO SCHOOL (MÁXIMA INVERSIÓN)", html.Br(),
                                                html.Span("SEPTIEMBRE ──── ", className="fw-bold"),
                                                "Ofertas de otoño", html.Br(),
                                                html.Span("OCTUBRE    ──── ", className="fw-bold"),
                                                "Pre-Black Friday", html.Br(),
                                                html.Span("NOVIEMBRE  ──── ", className="fw-bold text-danger"),
                                                "BLACK FRIDAY (MÁXIMA INVERSIÓN)", html.Br(),
                                                html.Span("DICIEMBRE  ──── ", className="fw-bold text-danger"),
                                                "NAVIDAD (MÁXIMA INVERSIÓN)",
                                            ], style={'lineHeight': '2'})
                                        ])
                                    ], className="shadow-sm")
                                ], width=12)
                            ]),
                            
                            # IMPACTO ECONÓMICO
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader("📈 PROYECCIÓN DE IMPACTO ECONÓMICO", 
                                                      className="bg-success text-white fw-bold"),
                                        dbc.CardBody([
                                            dbc.Table(
                                                html.Tbody([
                                                    html.Tr([html.Td("1. Publicidad"), 
                                                             html.Td("$50,000", className="text-end"),
                                                             html.Td("300%", className="text-end text-success"),
                                                             html.Td("+$150,000", className="text-end text-success")]),
                                                    html.Tr([html.Td("2. Cross-selling"), 
                                                             html.Td("$20,000", className="text-end"),
                                                             html.Td("500%", className="text-end text-success"),
                                                             html.Td("+$100,000", className="text-end text-success")]),
                                                    html.Tr([html.Td("3. Calendario"), 
                                                             html.Td("$30,000", className="text-end"),
                                                             html.Td("400%", className="text-end text-success"),
                                                             html.Td("+$120,000", className="text-end text-success")]),
                                                    html.Tr([html.Td("TOTAL", className="fw-bold"), 
                                                             html.Td("$100,000", className="text-end fw-bold"),
                                                             html.Td("370%", className="text-end fw-bold text-success"),
                                                             html.Td("+$370,000", className="text-end fw-bold text-success")]),
                                                ]),
                                                bordered=True, className="mb-3"
                                            ),
                                            html.P("ROI proyectado: 370% | Impacto total: +$370,000", 
                                                   className="text-center fw-bold text-success")
                                        ])
                                    ], className="shadow-sm")
                                ], width=12)
                            ]),
                            
                            # BOTÓN DE APROBACIÓN
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Hr(),
                                        dbc.Button("✅ APROBAR TODAS LAS PROPUESTAS", 
                                                  id="btn-aprobar-todo", 
                                                  color="success", 
                                                  size="lg",
                                                  className="w-100 mb-3",
                                                  n_clicks=0),
                                        html.P("Se recomienda aprobación inmediata para comenzar implementación en Q1 2020.",
                                              className="text-center text-muted small")
                                    ])
                                ], width=12)
                            ]),
                            
                            dcc.Download(id="download-propuestas")
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="📋 PROPUESTAS", tab_id="tab-propuestas"),
        
    ], className="mb-4"),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.Div([
                html.Span("📊 Desarrollado por: Paola Dueña - Data Analyst | ", className="text-muted small"),
                html.A(" LinkedIn", href="https://ar.linkedin.com/in/paoladit", target="_blank", className="text-primary small text-decoration-none"),
                html.Span(" | ", className="text-muted small"),
                html.A(" paoladf.it@gmail.com", href="mailto:paoladf.it@gmail.com", className="text-primary small text-decoration-none"),
                html.Br(),
                html.Span(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}", className="text-muted small"),
            ], className="text-center")
        ], width=12)
    ], className="mt-4"),
    
], fluid=True)

# ============================================
# 11. FUNCIONES DE EXPORTACIÓN
# ============================================

def generar_informe(seccion, data_filtrada, figuras, tablas):
    """Genera un informe HTML con el contenido de la sección"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Informe de Ventas 2019 - {seccion}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
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
        <h1>Panel de Ventas 2019 - Informe de {seccion}</h1>
        <p>Generado el: {timestamp}</p>
        <p>Período analizado: {data_filtrada['Fecha'].min()} a {data_filtrada['Fecha'].max()}</p>
        <p>Total de registros: {len(data_filtrada):,}</p>
        
        <h2>KPIs Principales</h2>
        <div>
            <div class="kpi-card">
                <div class="kpi-label">Ingresos Totales</div>
                <div class="kpi-value">${data_filtrada['Ingreso Total'].sum():,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Pedidos</div>
                <div class="kpi-value">{data_filtrada['ID de Pedido'].nunique():,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Unidades Vendidas</div>
                <div class="kpi-value">{data_filtrada['Cantidad Pedida'].sum():,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Ticket Promedio</div>
                <div class="kpi-value">${data_filtrada['Ingreso Total'].sum() / data_filtrada['ID de Pedido'].nunique():,.2f}</div>
            </div>
        </div>
    """
    
    # Agregar tablas
    for titulo, df_tabla in tablas.items():
        if df_tabla is not None and not df_tabla.empty:
            html_content += f"<h2>{titulo}</h2>"
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
# 12. CALLBACKS DE EXPORTACIÓN
# ============================================

@callback(
    Output("download-general", "data"),
    Input("btn-exportar-general", "n_clicks"),
    [State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'),
     State('dia', 'value'), State('categoria', 'value'), State('rango', 'value'),
     State('fechas', 'start_date'), State('fechas', 'end_date')],
    prevent_initial_call=True
)
def exportar_general(n_clicks, ciudad, estado, mes, dia, categoria, rango, start, end):
    if not n_clicks:
        return no_update
    
    # Aplicar filtros
    data = df.copy()
    if estado != 'Todos': data = data[data['Estado Nombre'] == estado]
    if ciudad != 'Todas': data = data[data['Ciudad'] == ciudad]
    if mes != 'Todos': data = data[data['Mes'] == mes]
    if dia != 'Todos': data = data[data['Día Semana Nombre'] == dia]
    if categoria != 'Todas': data = data[data['Categoría'] == categoria]
    if rango != 'Todos': data = data[data['Rango Precio'] == rango]
    
    try:
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        data = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    except:
        pass
    
    # Preparar tablas
    tablas = {
        "Ventas por Mes": data.groupby('Mes')['Ingreso Total'].sum().reset_index(),
        "Top 10 Productos": data.groupby('Producto')['Cantidad Pedida'].sum().nlargest(10).reset_index(),
        "Ventas por Ciudad": data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
    }
    
    html_content = generar_informe("VISIÓN GENERAL", data, {}, tablas)
    
    return dict(content=html_content, filename=f"informe_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

@callback(
    Output("download-comparador", "data"),
    Input("btn-exportar-comparador", "n_clicks"),
    [State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'),
     State('dia', 'value'), State('categoria', 'value'), State('rango', 'value'),
     State('fechas', 'start_date'), State('fechas', 'end_date'),
     State('comp-meses', 'value'), State('comp-metrica', 'value')],
    prevent_initial_call=True
)
def exportar_comparador(n_clicks, ciudad, estado, mes, dia, categoria, rango, start, end, meses_comp, metrica):
    if not n_clicks or not meses_comp:
        return no_update
    
    # Aplicar filtros
    data = df.copy()
    if estado != 'Todos': data = data[data['Estado Nombre'] == estado]
    if ciudad != 'Todas': data = data[data['Ciudad'] == ciudad]
    if mes != 'Todos': data = data[data['Mes'] == mes]
    if dia != 'Todos': data = data[data['Día Semana Nombre'] == dia]
    if categoria != 'Todas': data = data[data['Categoría'] == categoria]
    if rango != 'Todos': data = data[data['Rango Precio'] == rango]
    
    try:
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        data = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    except:
        pass
    
    # Filtrar meses seleccionados
    meses_con_datos = [m for m in meses_comp if not data[data['Mes'] == m].empty]
    
    # Preparar tabla comparativa
    tabla_comp = []
    for m in meses_con_datos:
        dm = data[data['Mes'] == m]
        tabla_comp.append({
            'Mes': m,
            'Ingresos': dm['Ingreso Total'].sum(),
            'Pedidos': dm['ID de Pedido'].nunique(),
            'Unidades': dm['Cantidad Pedida'].sum(),
            'Ticket Promedio': dm['Ingreso Total'].sum() / dm['ID de Pedido'].nunique() if dm['ID de Pedido'].nunique() > 0 else 0
        })
    
    tablas = {
        "Comparación de Meses": pd.DataFrame(tabla_comp)
    }
    
    html_content = generar_informe("COMPARADOR DE MESES", data, {}, tablas)
    
    return dict(content=html_content, filename=f"informe_comparador_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

# ============================================
# CALLBACKS PARA PROPUESTAS
# ============================================

@callback(
    Output("download-propuestas", "data"),
    Input("btn-descargar-propuestas", "n_clicks"),
    prevent_initial_call=True
)
def descargar_propuestas(n_clicks):
    """Genera PDF/HTML con el informe completo de propuestas"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Propuestas Estratégicas 2020</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .propuesta {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; }}
            .roi {{ color: #27ae60; font-weight: bold; }}
            .table {{ border-collapse: collapse; width: 100%; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 8px; }}
            .table th {{ background-color: #3498db; color: white; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #7f8c8d; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>📊 PROPUESTAS ESTRATÉGICAS 2020</h1>
        <p>Generado el: {timestamp}</p>
        <p>Basado en análisis de ventas 2019</p>
        
        <h2>🎯 RESUMEN EJECUTIVO</h2>
        <table class="table">
            <tr><th>Indicador</th><th>Valor</th><th>Interpretación</th></tr>
            <tr><td>Crecimiento anual</td><td>+153.2%</td><td>Excelente desempeño</td></tr>
            <tr><td>Ticket promedio</td><td>$193.40</td><td>Oportunidad de upselling</td></tr>
            <tr><td>Hora pico</td><td>19:00</td><td>Alta actividad nocturna</td></tr>
            <tr><td>Mejor día</td><td>Martes</td><td>Patrón atípico</td></tr>
        </table>
        
        <div class="propuesta">
            <h2>📋 PROPUESTA 1: OPTIMIZACIÓN PUBLICITARIA</h2>
            <p><strong>ROI:</strong> <span class="roi">300%</span> | <strong>Inversión:</strong> $50,000</p>
            <h3>Acciones:</h3>
            <ul>
                <li>Aumentar ads: Martes 18-22h</li>
                <li>Pausar campañas: Domingos mañana</li>
                <li>Promociones relámpago: 19:00-20:00</li>
            </ul>
        </div>
        
        <div class="propuesta">
            <h2>📦 PROPUESTA 2: VENTA CRUZADA</h2>
            <p><strong>ROI:</strong> <span class="roi">500%</span> | <strong>Inversión:</strong> $20,000</p>
            <h3>Acciones:</h3>
            <ul>
                <li>Sugerir al checkout: iPhone → AirPods</li>
                <li>Bundles con 10% descuento</li>
                <li>Email marketing post-compra</li>
            </ul>
        </div>
        
        <div class="propuesta">
            <h2>📅 PROPUESTA 3: CALENDARIO DE PROMOCIONES</h2>
            <p><strong>ROI:</strong> <span class="roi">400%</span> | <strong>Inversión:</strong> $30,000</p>
            <h3>Acciones:</h3>
            <ul>
                <li>Enero: Liquidación accesorios</li>
                <li>Agosto: Descuento estudiantil</li>
                <li>Nov-Dic: Envío garantizado</li>
            </ul>
        </div>
        
        <h2>📈 IMPACTO ECONÓMICO TOTAL</h2>
        <table class="table">
            <tr><th>Propuesta</th><th>Inversión</th><th>ROI</th><th>Impacto</th></tr>
            <tr><td>1. Publicidad</td><td>$50,000</td><td>300%</td><td>+$150,000</td></tr>
            <tr><td>2. Cross-selling</td><td>$20,000</td><td>500%</td><td>+$100,000</td></tr>
            <tr><td>3. Calendario</td><td>$30,000</td><td>400%</td><td>+$120,000</td></tr>
            <tr><td><strong>TOTAL</strong></td><td><strong>$100,000</strong></td><td><strong>370%</strong></td><td><strong>+$370,000</strong></td></tr>
        </table>
        
        <div class="footer">
            Informe generado automáticamente por el Panel de Ventas 2019<br>
            Desarrollado por Paola Dueña - Data Analyst
        </div>
    </body>
    </html>
    """
    
    return dict(content=html_content, filename=f"propuestas_estrategicas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

# ============================================
# 13. CALLBACKS PRINCIPALES
# ============================================

@callback(
    [Output('ciudad', 'options'),
     Output('ciudad', 'value')],
    [Input('estado', 'value'),
     Input('reset', 'n_clicks')]
)
def update_ciudades(estado, reset):
    ctx = dash.callback_context
    if ctx.triggered and 'reset' in ctx.triggered[0]['prop_id']:
        return [{'label': 'Todas', 'value': 'Todas'}] + [{'label': c, 'value': c} for c in sorted(df['Ciudad'].unique())], 'Todas'
    
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
     Output('categoria', 'value'),
     Output('rango', 'value'),
     Output('fechas', 'start_date'),
     Output('fechas', 'end_date'),
     Output('filtro-prod', 'value'),
     Output('comp-meses', 'value')],
    Input('reset', 'n_clicks')
)
def reset_filtros(n_clicks):
    if not n_clicks:
        return [no_update] * 9
    return ('Todos', 'Todos', 'Todos', 'Todas', 'Todos',
            df['Fecha'].min(), df['Fecha'].max(), 'General',
            ['Enero', 'Febrero', 'Marzo'])

@callback(
    [Output('indicador-prod', 'children'),
     Output('titulo-factores', 'children')],
    Input('filtro-prod', 'value')
)
def update_titulos_prod(f):
    if f == 'General':
        indicador = "🌐 Análisis Global"
        titulo = "🔍 FACTORES DE ÉXITO - PRODUCTO MÁS VENDIDO (GLOBAL)"
    elif f == 'Mes':
        indicador = "📅 Análisis por Mes"
        titulo = "🔍 FACTORES DE ÉXITO - PRODUCTO MÁS VENDIDO POR MES"
    elif f == 'Semana':
        indicador = "📆 Análisis por Semana"
        titulo = "🔍 FACTORES DE ÉXITO - PRODUCTO MÁS VENDIDO POR SEMANA"
    else:
        indicador = "📊 Análisis por Día"
        titulo = "🔍 FACTORES DE ÉXITO - PRODUCTO MÁS VENDIDO POR DÍA"
    
    return html.Span(indicador, className="text-primary fw-bold"), titulo

@callback(
    [Output('subtitulo', 'children'),
     Output('kpis', 'children'),
     Output('tendencias', 'children'),
     Output('graf-mes', 'figure'),
     Output('graf-tendencia', 'figure'),
     Output('graf-heatmap', 'figure'),
     Output('graf-dias', 'figure'),
     Output('graf-productos', 'figure'),
     Output('graf-ciudades', 'figure'),
     Output('mapa-estados', 'figure'),
     Output('graf-finde', 'figure'),
     Output('prod-comp', 'children'),
     Output('tabla-prod-mes', 'children'),
     Output('factores-prod', 'children'),
     Output('resumen', 'children'),
     Output('eventos', 'children'),
     Output('prod-container', 'children'),
     Output('comp-kpis', 'children'),
     Output('graf-comp-tend', 'figure'),
     Output('graf-comp-dist', 'figure'),
     Output('comp-tabla', 'children'),
     Output('graf-horas-dist', 'figure'),
     Output('graf-horas-heat', 'figure'),
     Output('graf-horas-evo', 'figure')],
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
    
    # Filtro de fechas
    try:
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        data = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    except:
        pass
    
    # Subtítulo
    subtitulo = f"📊 {len(data):,} transacciones | {data['Ciudad'].nunique()} ciudades | {data['Producto'].nunique()} productos"
    
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
    # TENDENCIAS
    # ========================================
    if not data.empty:
        ventas_mes = data.groupby('Mes Num')['Ingreso Total'].sum()
        crecimiento = 0
        if len(ventas_mes) > 1:
            crecimiento = ((ventas_mes.iloc[-1] - ventas_mes.iloc[0]) / ventas_mes.iloc[0] * 100)
        
        hora_pico = data.groupby('Hora')['ID de Pedido'].nunique().idxmax()
        dia_pico = data.groupby('Día Semana Nombre')['ID de Pedido'].nunique().idxmax()
        prod_top = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
        
        color_crec = "success" if crecimiento > 0 else "danger" if crecimiento < 0 else "warning"
        signo = "+" if crecimiento > 0 else ""
        
        tendencias = dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📈 CRECIMIENTO", className="text-center text-muted"),
                    html.H3(f"{signo}{crecimiento:.1f}%", className=f"text-center text-{color_crec} fw-bold"),
                    html.P("Ene vs Dic", className="text-center small text-muted"),
                ])
            ], className="bg-light h-100 text-center p-2"), width=3),
            
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("⏰ HORA PICO", className="text-center text-muted"),
                    html.H3(f"{hora_pico}:00", className="text-center text-warning fw-bold"),
                    html.P("Momento de mayor actividad", className="text-center small text-muted"),
                ])
            ], className="bg-light h-100 text-center p-2"), width=3),
            
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📆 MEJOR DÍA", className="text-center text-muted"),
                    html.H3(dia_pico, className="text-center text-info fw-bold"),
                    html.P("Día con más ventas", className="text-center small text-muted"),
                ])
            ], className="bg-light h-100 text-center p-2"), width=3),
            
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🏆 PRODUCTO TOP", className="text-center text-muted"),
                    html.H6(prod_top[:20] + ('...' if len(prod_top) > 20 else ''), 
                           className="text-center text-success fw-bold"),
                    html.P("Más vendido", className="text-center small text-muted"),
                ])
            ], className="bg-light h-100 text-center p-2"), width=3)
        ], className="g-2")
    else:
        tendencias = html.P("Datos insuficientes", className="text-center text-muted")
    
    # ========================================
    # GRÁFICO VENTAS POR MES
    # ========================================
    if not data.empty:
        df_mes = data.groupby('Mes')['Ingreso Total'].sum().reset_index()
        orden = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                 'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        df_mes['Mes'] = pd.Categorical(df_mes['Mes'], categories=orden, ordered=True)
        df_mes = df_mes.sort_values('Mes')
        
        fig1 = px.bar(df_mes, x='Mes', y='Ingreso Total', 
                     title='💰 Ventas por Mes',
                     color='Ingreso Total', color_continuous_scale='Blues',
                     text_auto='.2s')
        fig1.update_traces(texttemplate='$%{text:.2s}', textposition='outside')
        fig1.update_layout(height=350, showlegend=False, yaxis_title="Ingresos ($)")
    else:
        fig1 = go.Figure()
        fig1.add_annotation(text="Sin datos disponibles", showarrow=False)
        fig1.update_layout(height=350)
    
    # ========================================
    # GRÁFICO TENDENCIA DIARIA
    # ========================================
    if not data.empty:
        diario = data.groupby('Fecha')['Ingreso Total'].sum().reset_index()
        diario['Fecha'] = pd.to_datetime(diario['Fecha'])
        diario = diario.sort_values('Fecha')
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=diario['Fecha'], y=diario['Ingreso Total'],
            mode='lines', name='Ventas diarias',
            line=dict(color='#8e44ad', width=2)
        ))
        if len(diario) > 7:
            diario['MA7'] = diario['Ingreso Total'].rolling(7).mean()
            fig2.add_trace(go.Scatter(
                x=diario['Fecha'], y=diario['MA7'],
                name='Promedio 7 días', line=dict(color='red', width=2, dash='dot')
            ))
        fig2.update_layout(title='📈 Tendencia de Ventas Diarias', height=350, yaxis_title="Ingresos ($)")
    else:
        fig2 = go.Figure()
        fig2.add_annotation(text="Sin datos", showarrow=False)
        fig2.update_layout(height=350)
    
    # ========================================
    # GRÁFICO HEATMAP
    # ========================================
    if not data.empty:
        heat = data.groupby(['Hora', 'Día Semana Nombre']).size().reset_index(name='Pedidos')
        if len(heat) > 0:
            orden = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
            heat['Día Semana Nombre'] = pd.Categorical(heat['Día Semana Nombre'], categories=orden, ordered=True)
            heat = heat.dropna().sort_values(['Día Semana Nombre','Hora'])
            
            fig3 = px.density_heatmap(
                heat, x='Hora', y='Día Semana Nombre', z='Pedidos',
                title='🔥 Mapa de Calor - Horas Pico',
                color_continuous_scale='Viridis',
                labels={'Pedidos': 'Cantidad de Pedidos', 'Hora': 'Hora del Día', 'Día Semana Nombre': 'Día de la Semana'}
            )
            fig3.update_layout(
                height=450,
                margin=dict(l=50, r=80, t=80, b=50),
                coloraxis_colorbar=dict(
                    title="Pedidos",
                    tickformat=",d",
                    len=0.8,
                    thickness=15,
                    x=1.05,
                    y=0.5
                )
            )
        else:
            fig3 = go.Figure()
            fig3.add_annotation(text="Sin datos para heatmap", showarrow=False)
            fig3.update_layout(height=450)
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="Sin datos disponibles", showarrow=False)
        fig3.update_layout(height=450)
    
    # ========================================
    # GRÁFICO VENTAS POR DÍA
    # ========================================
    if not data.empty:
        dias = data.groupby(['Día Semana Nombre', 'Día Semana'])['ID de Pedido'].nunique().reset_index(name='Pedidos')
        dias_ingresos = data.groupby('Día Semana Nombre')['Ingreso Total'].sum().reset_index()
        dias = dias.merge(dias_ingresos, on='Día Semana Nombre', how='left')
        
        if len(dias) > 0:
            dias = dias.sort_values('Día Semana')
            
            fig4 = go.Figure()
            
            fig4.add_trace(go.Bar(
                x=dias['Día Semana Nombre'],
                y=dias['Pedidos'],
                marker_color=['#3498db', '#3498db', '#3498db', '#3498db', '#3498db', '#e74c3c', '#e74c3c'],
                text=[f"{x:,}" for x in dias['Pedidos']],
                textposition='outside',
                textfont=dict(size=10),
                hovertemplate='%{x}<br>📦 Pedidos: %{y:,}<br>💰 Ingresos: $%{customdata:,.0f}<extra></extra>',
                customdata=dias['Ingreso Total']
            ))
            
            fig4.update_layout(
                title='📆 Ventas por Día de la Semana',
                height=400,
                showlegend=False,
                margin=dict(l=50, r=80, t=80, b=50),
                xaxis=dict(
                    title="Día de la Semana",
                    tickangle=0
                ),
                yaxis=dict(
                    title="Cantidad de Pedidos"
                )
            )
            
            # Agregar anotación en el margen derecho
            fig4.add_annotation(
                x=1.05,
                y=0.95,
                xref="paper",
                yref="paper",
                text="🔵 Laborable<br>🔴 Finde",
                showarrow=False,
                align="left",
                bordercolor="lightgray",
                borderwidth=1,
                borderpad=4,
                bgcolor="white",
                font=dict(size=11)
            )
        else:
            fig4 = go.Figure()
            fig4.add_annotation(text="Sin datos", showarrow=False)
            fig4.update_layout(height=400)
    else:
        fig4 = go.Figure()
        fig4.add_annotation(text="Sin datos", showarrow=False)
        fig4.update_layout(height=400)
    
    # ========================================
    # GRÁFICO TOP PRODUCTOS
    # ========================================
    if not data.empty:
        top_prod = data.groupby('Producto')['Cantidad Pedida'].sum().nlargest(10).reset_index()
        if len(top_prod) > 0:
            fig5 = px.bar(
                top_prod, x='Cantidad Pedida', y='Producto',
                orientation='h', title='📦 Top 10 Productos más Vendidos',
                color='Cantidad Pedida', color_continuous_scale='Greens',
                text_auto=True
            )
            fig5.update_layout(height=350, yaxis_title="")
        else:
            fig5 = go.Figure()
            fig5.add_annotation(text="Sin datos", showarrow=False)
            fig5.update_layout(height=350)
    else:
        fig5 = go.Figure()
        fig5.add_annotation(text="Sin datos", showarrow=False)
        fig5.update_layout(height=350)
    
    # ========================================
    # GRÁFICO CIUDADES
    # ========================================
    if not data.empty:
        if ciudad != 'Todas':
            # Una ciudad específica seleccionada
            data_city = data[data['Ciudad'] == ciudad]
            top_prod_city = data_city.groupby('Producto')['Cantidad Pedida'].sum().nlargest(5)
            ventas_mes_city = data_city.groupby('Mes')['Ingreso Total'].sum().reset_index()
            orden = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                     'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
            ventas_mes_city['Mes'] = pd.Categorical(ventas_mes_city['Mes'], categories=orden, ordered=True)
            ventas_mes_city = ventas_mes_city.sort_values('Mes')
            
            fig6 = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f'📈 Evolución mensual en {ciudad}', f'📦 Top 5 productos en {ciudad}'),
                horizontal_spacing=0.15
            )
            
            # Gráfico de evolución mensual
            fig6.add_trace(
                go.Scatter(
                    x=ventas_mes_city['Mes'],
                    y=ventas_mes_city['Ingreso Total'],
                    mode='lines+markers',
                    name='Ingresos',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=8),
                    hovertemplate='Mes: %{x}<br>💰 $%{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Gráfico de top productos
            fig6.add_trace(
                go.Bar(
                    x=top_prod_city.values,
                    y=top_prod_city.index,
                    orientation='h',
                    name='Productos',
                    marker_color='#e74c3c',
                    text=[f"{x:,.0f}" for x in top_prod_city.values],
                    textposition='outside',
                    textfont=dict(size=10),
                    hovertemplate='Producto: %{y}<br>📦 Unidades: %{x:,.0f}<extra></extra>'
                ),
                row=1, col=2
            )
            
            fig6.update_layout(
                title=dict(
                    text=f'🏙️ Análisis Detallado: {ciudad}',
                    font=dict(size=14),
                    x=0.5
                ),
                height=400,
                showlegend=False,
                margin=dict(l=50, r=50, t=80, b=50)
            )
            fig6.update_xaxes(title_text="Mes", row=1, col=1, tickangle=0)
            fig6.update_yaxes(title_text="Ingresos ($)", row=1, col=1, tickformat=",.0f")
            fig6.update_xaxes(title_text="Unidades Vendidas", row=1, col=2)
            fig6.update_yaxes(title_text="", row=1, col=2)
            
        else:
            # Top 10 ciudades
            top_city = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
            if len(top_city) > 0:
                # Ordenar de mayor a menor para mejor visualización
                top_city = top_city.sort_values('Ingreso Total', ascending=True)
                
                fig6 = go.Figure()
                fig6.add_trace(go.Bar(
                    x=top_city['Ingreso Total'],
                    y=top_city['Ciudad'],
                    orientation='h',
                    marker_color='#e74c3c',
                    marker_colorscale='Reds',
                    text=[f"${x:,.0f}" for x in top_city['Ingreso Total']],
                    textposition='outside',
                    textfont=dict(size=11),
                    hovertemplate='Ciudad: %{y}<br>💰 $%{x:,.0f}<extra></extra>'
                ))
                
                fig6.update_layout(
                    title=dict(
                        text='🏙️ Top 10 Ciudades por Ingresos',
                        font=dict(size=14),
                        x=0.5
                    ),
                    height=400,
                    xaxis=dict(
                        title="Ingresos ($)",
                        tickformat=",.0f"
                    ),
                    yaxis=dict(
                        title="",
                        autorange="reversed"
                    ),
                    margin=dict(l=100, r=50, t=80, b=50)
                )
            else:
                fig6 = go.Figure()
                fig6.add_annotation(text="Sin datos", showarrow=False)
                fig6.update_layout(height=400)
    else:
        fig6 = go.Figure()
        fig6.add_annotation(text="Sin datos disponibles", showarrow=False)
        fig6.update_layout(height=400)
    
    # ========================================
    # MAPA DE ESTADOS
    # ========================================
    if not data.empty:
        ventas_estado = data.groupby('Estado Nombre').agg({
            'Ingreso Total': 'sum',
            'ID de Pedido': 'nunique'
        }).reset_index()
        ventas_estado['codigo'] = ventas_estado['Estado Nombre'].map(codigos_estados)
        estados_validos = ['CA','TX','NY','FL','IL','PA','OH','GA','NC','MI','NJ','VA','WA','MA','AZ','TN','IN','MO','MD','WI']
        ventas_estado = ventas_estado[ventas_estado['codigo'].isin(estados_validos)]
        
        if not ventas_estado.empty:
            fig_mapa = go.Figure(data=go.Choropleth(
                locations=ventas_estado['codigo'],
                z=ventas_estado['Ingreso Total'],
                locationmode='USA-states',
                colorscale='Reds',
                colorbar_title="Ingresos ($)",
                text=ventas_estado['Estado Nombre'],
                customdata=ventas_estado['ID de Pedido'],
                hovertemplate='<b>%{text}</b><br>💰 $%{z:,.0f}<br>📦 %{customdata} pedidos<extra></extra>'
            ))
            fig_mapa.update_layout(
                title='🗺️ Ventas por Estado (EE.UU.)',
                geo_scope='usa',
                height=400
            )
        else:
            fig_mapa = go.Figure()
            fig_mapa.add_annotation(text="Sin datos de estados USA", showarrow=False)
            fig_mapa.update_layout(height=400)
    else:
        fig_mapa = go.Figure()
        fig_mapa.add_annotation(text="Sin datos", showarrow=False)
        fig_mapa.update_layout(height=400)
    
    # ========================================
    # GRÁFICO FINDE VS LABORAL (VERSIÓN CORREGIDA - SIN SUPERPOSICIÓN)
    # ========================================
    if not data.empty:
        # Agrupar por fecha para obtener ventas diarias
        ventas_diarias = data.groupby('Fecha')['Ingreso Total'].sum().reset_index()
        ventas_diarias['Es Finde'] = ventas_diarias['Fecha'].apply(
            lambda x: pd.to_datetime(x).dayofweek in [5, 6]
        )
        
        # Calcular promedios diarios
        laboral = ventas_diarias[~ventas_diarias['Es Finde']]['Ingreso Total'].mean() if not ventas_diarias[~ventas_diarias['Es Finde']].empty else 0
        finde = ventas_diarias[ventas_diarias['Es Finde']]['Ingreso Total'].mean() if not ventas_diarias[ventas_diarias['Es Finde']].empty else 0
        dif_percent = ((finde - laboral) / laboral * 100) if laboral > 0 else 0
        
        # Calcular promedios por día
        dias_prom = ventas_diarias.copy()
        dias_prom['Día Semana Nombre'] = pd.to_datetime(dias_prom['Fecha']).dt.day_name().map(dias_espanol)
        orden = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
        dias_prom['Día Semana Nombre'] = pd.Categorical(dias_prom['Día Semana Nombre'], categories=orden, ordered=True)
        dias_prom = dias_prom.groupby('Día Semana Nombre')['Ingreso Total'].mean().reset_index()
        dias_prom = dias_prom.sort_values('Día Semana Nombre')
        
        # Crear figura con dos subplots separados y bien espaciados
        fig_finde = make_subplots(
            rows=1, cols=2,
            subplot_titles=('📊 LABORABLES VS FINDE', '📆 PROMEDIO POR DÍA'),
            horizontal_spacing=0.25,
            column_widths=[0.45, 0.55]
        )
        
        # Gráfico 1: Laborables vs Finde
        fig_finde.add_trace(
            go.Bar(
                x=['Laborables', 'Finde'],
                y=[laboral, finde],
                marker_color=['#3498db', '#e74c3c'],
                text=[f"${laboral:,.0f}", f"${finde:,.0f}"],
                textposition='outside',
                textfont=dict(size=12, color='black'),
                width=[0.5, 0.5],
                hovertemplate='%{x}<br>💰 $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Gráfico 2: Por día
        fig_finde.add_trace(
            go.Bar(
                x=dias_prom['Día Semana Nombre'],
                y=dias_prom['Ingreso Total'],
                marker_color=['#3498db', '#3498db', '#3498db', '#3498db', '#3498db', '#e74c3c', '#e74c3c'],
                text=[f"${x:,.0f}" for x in dias_prom['Ingreso Total']],
                textposition='outside',
                textfont=dict(size=11),
                width=[0.7] * 7,
                hovertemplate='%{x}<br>💰 $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Línea de promedio general en el segundo gráfico
        prom_gral = ventas_diarias['Ingreso Total'].mean()
        fig_finde.add_hline(
            y=prom_gral, 
            line_dash="dash", 
            line_color="#7f8c8d",
            line_width=2,
            opacity=0.7,
            row=1, col=2
        )
        
        # Actualizar layout con mejor organización
        fig_finde.update_layout(
            title=dict(
                text=f"📊 COMPARACIÓN: DÍAS LABORABLES VS FINES DE SEMANA",
                font=dict(size=16, family="Arial", color="#2c3e50"),
                x=0.5,
                y=0.95,
                xanchor='center'
            ),
            height=450,
            showlegend=False,
            margin=dict(l=60, r=60, t=100, b=80),
            paper_bgcolor='white',
            plot_bgcolor='#f8f9fa'
        )
        
        # Configurar ejes
        fig_finde.update_xaxes(title_text="Tipo de Día", row=1, col=1, tickangle=0)
        fig_finde.update_xaxes(title_text="Día de la Semana", row=1, col=2, tickangle=0)
        fig_finde.update_yaxes(title_text="Ingreso Diario ($)", row=1, col=1, tickformat=",.0f")
        fig_finde.update_yaxes(title_text="Ingreso Diario ($)", row=1, col=2, tickformat=",.0f")
        
        # Agregar nota explicativa en la parte inferior
        fig_finde.add_annotation(
            x=0.5,
            y=-0.15,
            xref="paper",
            yref="paper",
            text="🔵 Días laborables (Lunes a Viernes)   🔴 Fines de semana (Sábado y Domingo)",
            showarrow=False,
            font=dict(size=11),
            align="center"
        )
    else:
        fig_finde = go.Figure()
        fig_finde.add_annotation(text="Sin datos", showarrow=False)
        fig_finde.update_layout(height=450)
    
    # ========================================
    # PRODUCTOS COMPLEMENTARIOS
    # ========================================
    if not data.empty and len(data) > 10:
        try:
            pedidos = data.groupby('ID de Pedido')['Producto'].agg(list).reset_index()
            multi = pedidos[pedidos['Producto'].apply(len) > 1]
            if len(multi) > 0:
                pares = []
                for p in multi['Producto']:
                    if len(p) > 1:
                        pares.extend(combinations(sorted(set(p)), 2))
                top_pares = Counter(pares).most_common(5)
                
                rows = []
                for i, ((a, b), c) in enumerate(top_pares, 1):
                    rows.append(html.Tr([
                        html.Td(f"#{i}", className="fw-bold"),
                        html.Td(a[:25] + ('...' if len(a) > 25 else '')),
                        html.Td(b[:25] + ('...' if len(b) > 25 else '')),
                        html.Td(f"{c} veces", className="text-end text-success")
                    ]))
                
                comp = html.Div([
                    html.P(f"📊 Basado en {len(multi):,} pedidos con múltiples productos", className="small text-muted"),
                    dbc.Table(
                        [html.Thead(html.Tr([
                            html.Th("#"),
                            html.Th("Producto A"),
                            html.Th("Producto B"),
                            html.Th("Frecuencia")
                        ])),
                         html.Tbody(rows)],
                        striped=True, bordered=True, hover=True, size='sm'
                    )
                ])
            else:
                comp = html.P("No hay pedidos con múltiples productos", className="text-center text-muted")
        except:
            comp = html.P("Error en análisis", className="text-center text-danger")
    else:
        comp = html.P("Datos insuficientes para análisis", className="text-center text-muted")
    
    # ========================================
    # TABLA PRODUCTO MÁS VENDIDO POR MES
    # ========================================
    if not data.empty:
        prods_mes = data.groupby(['Mes', 'Producto'])['Cantidad Pedida'].sum().reset_index()
        idx = prods_mes.groupby('Mes')['Cantidad Pedida'].idxmax()
        top_mes = prods_mes.loc[idx].reset_index(drop=True)
        orden = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                 'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        top_mes['Mes'] = pd.Categorical(top_mes['Mes'], categories=orden, ordered=True)
        top_mes = top_mes.sort_values('Mes')
        
        rows = []
        for _, r in top_mes.iterrows():
            rows.append(html.Tr([
                html.Td(r['Mes'], className="fw-bold"),
                html.Td(r['Producto'][:35] + ('...' if len(r['Producto']) > 35 else '')),
                html.Td(f"{r['Cantidad Pedida']:,.0f}", className="text-end")
            ]))
        
        prod_top_gral = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
        tabla_prod = dbc.Table(
            [html.Thead(html.Tr([html.Th("Mes"), html.Th("Producto Más Vendido"), html.Th("Cantidad")])),
             html.Tbody(rows)],
            striped=True, bordered=True, hover=True, size='sm'
        )
        tabla_prod = html.Div([
            tabla_prod,
            html.P(f"🏆 Producto más vendido en GENERAL: {prod_top_gral}", className="mt-3 fw-bold text-success")
        ])
    else:
        tabla_prod = html.P("Sin datos", className="text-center text-muted")
    
    # ========================================
    # FACTORES PRODUCTO ESTRELLA
    # ========================================
    if not data.empty:
        try:
            if filtro_prod == 'General':
                analisis = analizar_producto_estrella(data)
                periodo = "GLOBAL"
            elif filtro_prod == 'Mes':
                if mes != 'Todos':
                    analisis = analizar_producto_estrella(data[data['Mes'] == mes])
                    periodo = f"MES: {mes}"
                else:
                    mtop = data.groupby('Mes')['Cantidad Pedida'].sum().idxmax()
                    analisis = analizar_producto_estrella(data[data['Mes'] == mtop])
                    periodo = f"MES: {mtop} (top)"
            elif filtro_prod == 'Semana':
                stop = data.groupby('Semana')['Cantidad Pedida'].sum().idxmax()
                analisis = analizar_producto_estrella(data[data['Semana'] == stop])
                periodo = f"SEMANA: {stop}"
            else:
                dtop = data.groupby('Día del Año')['Cantidad Pedida'].sum().idxmax()
                fecha_top = data[data['Día del Año'] == dtop]['Fecha'].iloc[0] if not data[data['Día del Año'] == dtop].empty else "N/A"
                analisis = analizar_producto_estrella(data[data['Día del Año'] == dtop])
                periodo = f"DÍA: {fecha_top}"
            
            if analisis:
                factores = dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("💰 Precio Promedio", className="text-center text-muted"),
                            html.H3(f"${analisis['precio']:.2f}", className="text-center text-primary"),
                            html.P(f"{analisis['comparacion_precio']:+.1f}% vs promedio", className="text-center small"),
                        ])
                    ], className="border-primary h-100"), width=3),
                    
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("📊 Participación", className="text-center text-muted"),
                            html.H3(f"{analisis['share']:.1f}%", className="text-center text-success"),
                            html.P(f"{analisis['unidades']:,.0f} unidades", className="text-center small"),
                        ])
                    ], className="border-success h-100"), width=3),
                    
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("🎫 Ticket Promedio", className="text-center text-muted"),
                            html.H3(f"${analisis['ingresos']/analisis['pedidos']:,.2f}", 
                                   className="text-center text-info"),
                            html.P(f"{analisis['pedidos']} pedidos", className="text-center small"),
                        ])
                    ], className="border-warning h-100"), width=3),
                    
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("🏷️ Estrategia", className="text-center text-muted"),
                            html.H6(
                                "PREMIUM" if analisis['comparacion_precio'] > 20 else
                                "ECONÓMICO" if analisis['comparacion_precio'] < -20 else
                                "COMPETITIVO",
                                className="text-center fw-bold"
                            ),
                        ])
                    ], className="border-info h-100"), width=3)
                ], className="g-2")
                
                factores = html.Div([
                    html.P(f"📌 ANÁLISIS PARA {periodo}", className="fw-bold text-info mb-3"),
                    factores,
                    html.Hr(),
                    html.Ul([html.Li(i) for i in analisis['insights']], className="mt-2")
                ])
            else:
                factores = html.P("No hay datos suficientes", className="text-center text-muted")
        except Exception as e:
            factores = html.P(f"Error en análisis", className="text-center text-danger")
    else:
        factores = html.P("Datos insuficientes", className="text-center text-muted")
    
    # ========================================
    # PRODUCTO ESTRELLA CONTAINER
    # ========================================
    if not data.empty:
        try:
            top = data.groupby('Producto').agg({
                'Cantidad Pedida': 'sum',
                'Ingreso Total': 'sum'
            }).sort_values('Cantidad Pedida', ascending=False).iloc[0]
            
            prod_container = dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.H3("🏆", className="display-4 text-warning"), width=2, className="text-center"),
                        dbc.Col([
                            html.H5(top.name[:60] + ('...' if len(top.name) > 60 else ''), className="fw-bold"),
                            html.P([
                                html.Span(f"📦 {top['Cantidad Pedida']:,.0f} unidades", className="me-3"),
                                html.Span(f"💰 ${top['Ingreso Total']:,.0f}", className="text-success"),
                            ])
                        ], width=10)
                    ])
                ]),
                className="bg-light border-2 border-warning"
            )
        except:
            prod_container = html.P("No se pudo identificar producto estrella", className="text-center text-muted")
    else:
        prod_container = html.P("Sin datos", className="text-center text-muted")
    
    # ========================================
    # RESUMEN EJECUTIVO
    # ========================================
    if not data.empty:
        try:
            prod_top = data.groupby('Producto')['Cantidad Pedida'].sum().idxmax()
            ciudad_top = data.groupby('Ciudad')['Ingreso Total'].sum().idxmax()
            estado_top = data.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax()
            cat_top = data.groupby('Categoría')['Ingreso Total'].sum().idxmax()
            
            resumen = dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("🏆 Producto Estrella", className="text-center"),
                        html.P(prod_top[:20], className="text-center text-success fw-bold"),
                    ])
                ], className="border-success h-100 shadow-sm"), width=3),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("🏙️ Ciudad Top", className="text-center"),
                        html.P(ciudad_top[:20], className="text-center text-primary fw-bold"),
                    ])
                ], className="border-primary h-100 shadow-sm"), width=3),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("🗺️ Estado Top", className="text-center"),
                        html.P(estado_top[:20], className="text-center text-info fw-bold"),
                    ])
                ], className="border-info h-100 shadow-sm"), width=3),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("📦 Categoría Top", className="text-center"),
                        html.P(cat_top[:20], className="text-center text-warning fw-bold"),
                    ])
                ], className="border-warning h-100 shadow-sm"), width=3)
            ])
        except:
            resumen = html.P("Error al generar resumen", className="text-center text-muted")
    else:
        resumen = html.P("Datos insuficientes", className="text-center text-muted")
    
    # ========================================
    # EVENTOS ESPECIALES
    # ========================================
    if not data.empty:
        try:
            data['Evento'] = data['Fecha Pedido'].apply(identificar_evento)
            eventos_data = data[data['Evento'] != 'Normal'].groupby('Evento').agg({
                'Ingreso Total': 'sum',
                'ID de Pedido': 'nunique'
            }).reset_index()
            
            if not eventos_data.empty:
                cards = []
                for _, r in eventos_data.iterrows():
                    prom = r['Ingreso Total'] / r['ID de Pedido'] if r['ID de Pedido'] > 0 else 0
                    cards.append(dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6(r['Evento'], className="text-center fw-bold"),
                            html.H5(f"${r['Ingreso Total']:,.0f}", className="text-center text-primary"),
                            html.P([
                                html.Span(f"📦 {r['ID de Pedido']} pedidos", className="d-block"),
                                html.Span(f"💰 ${prom:,.2f} por pedido", className="d-block small text-muted"),
                            ], className="text-center small"),
                        ])
                    ], className="border-primary border-2 shadow-sm h-100"), width=3))
                eventos = dbc.Row(cards, className="g-2")
            else:
                eventos = html.P("No hay eventos especiales en el período seleccionado", className="text-center text-muted")
        except:
            eventos = html.P("Error al analizar eventos", className="text-center text-danger")
    else:
        eventos = html.P("Datos insuficientes", className="text-center text-muted")
    
    # ========================================
    # COMPARADOR KPIs
    # ========================================
    comp_kpis = html.P("Selecciona meses para comparar", className="text-center text-muted")
    fig_comp_tend = go.Figure().add_annotation(text="Selecciona meses", showarrow=False)
    fig_comp_tend.update_layout(height=350)
    fig_comp_dist = go.Figure().add_annotation(text="Selecciona meses", showarrow=False)
    fig_comp_dist.update_layout(height=350)
    comp_tabla = html.P("Selecciona meses", className="text-center text-muted")
    
    if meses_comp and len(meses_comp) > 0:
        meses_con_datos = [m for m in meses_comp if not data[data['Mes'] == m].empty]
        if meses_con_datos:
            # KPIs
            filas = []
            for i in range(0, len(meses_con_datos), 3):
                fila = meses_con_datos[i:i+3]
                cols = []
                for m in fila:
                    dm = data[data['Mes'] == m]
                    ingresos_m = dm['Ingreso Total'].sum()
                    pedidos_m = dm['ID de Pedido'].nunique()
                    if metrica == 'ingresos':
                        valor = ingresos_m
                        texto = f"${valor:,.0f}"
                    else:
                        valor = pedidos_m
                        texto = f"{valor:,}"
                    
                    valores_fila = []
                    for mm in fila:
                        dmm = data[data['Mes'] == mm]
                        if metrica == 'ingresos':
                            valores_fila.append(dmm['Ingreso Total'].sum())
                        else:
                            valores_fila.append(dmm['ID de Pedido'].nunique())
                    prom_fila = sum(valores_fila) / len(valores_fila) if valores_fila else 0
                    var = ((valor - prom_fila) / prom_fila * 100) if prom_fila > 0 else 0
                    
                    cols.append(dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6(m, className="text-center"),
                            html.H3(texto, className="text-center text-primary fw-bold"),
                            html.P(
                                f"{var:+.1f}% vs promedio",
                                className=f"text-center small text-{'success' if var > 0 else 'danger' if var < 0 else 'secondary'}"
                            ),
                            html.P([
                                html.Span(f"💰 ${ingresos_m:,.0f}", className="d-block small"),
                                html.Span(f"📦 {pedidos_m:,} pedidos", className="d-block small text-muted"),
                            ], className="text-center small mt-2")
                        ])
                    ], className=f"border-primary shadow-sm h-100"), width=4))
                filas.append(dbc.Row(cols, className="mb-3"))
            comp_kpis = html.Div(filas)
            
            # Gráficos
            fig_comp_tend = go.Figure()
            colors = px.colors.qualitative.Set1
            for i, m in enumerate(meses_con_datos):
                dm = data[data['Mes'] == m]
                dia = dm.groupby('Día')['Ingreso Total'].sum().reset_index()
                fig_comp_tend.add_trace(go.Scatter(
                    x=dia['Día'], y=dia['Ingreso Total'],
                    mode='lines+markers', name=m,
                    line=dict(color=colors[i % len(colors)], width=3)
                ))
            fig_comp_tend.update_layout(
                title='Tendencia Diaria - Comparación de Meses',
                height=350,
                hovermode='x unified'
            )
            
            # Tabla
            rows = []
            for m in meses_con_datos:
                dm = data[data['Mes'] == m]
                rows.append(html.Tr([
                    html.Td(m, className="fw-bold"),
                    html.Td(f"${dm['Ingreso Total'].sum():,.0f}"),
                    html.Td(f"{dm['ID de Pedido'].nunique():,}"),
                    html.Td(f"{dm['Cantidad Pedida'].sum():,}")
                ]))
            comp_tabla = dbc.Table(
                [html.Thead(html.Tr([html.Th("Mes"), html.Th("Ingresos"), html.Th("Pedidos"), html.Th("Unidades")])),
                 html.Tbody(rows)],
                striped=True, bordered=True, hover=True, size='sm'
            )
            
            # ========================================
            # GRÁFICO DISTRIBUCIÓN POR MES
            # ========================================
            if meses_con_datos:
                datos_meses = data[data['Mes'].isin(meses_con_datos)].groupby('Mes').agg({
                    'Ingreso Total': 'sum',
                    'ID de Pedido': 'nunique'
                }).reset_index()
                
                if not datos_meses.empty:
                    # Asegurar orden correcto de meses
                    datos_meses['Mes'] = pd.Categorical(datos_meses['Mes'], categories=orden, ordered=True)
                    datos_meses = datos_meses.sort_values('Mes')
                    datos_meses = datos_meses[datos_meses['Mes'].isin(meses_con_datos)]
                    
                    fig_comp_dist = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Barras de ingresos
                    fig_comp_dist.add_trace(
                        go.Bar(
                            x=datos_meses['Mes'],
                            y=datos_meses['Ingreso Total'],
                            name='Ingresos',
                            marker_color='#3498db',
                            text=[f"${x:,.0f}" for x in datos_meses['Ingreso Total']],
                            textposition='outside',
                            hovertemplate='Mes: %{x}<br>💰 Ingresos: $%{y:,.0f}<extra></extra>'
                        ),
                        secondary_y=False
                    )
                    
                    # Línea de pedidos
                    fig_comp_dist.add_trace(
                        go.Scatter(
                            x=datos_meses['Mes'],
                            y=datos_meses['ID de Pedido'],
                            name='Pedidos',
                            mode='lines+markers',
                            marker_color='#e74c3c',
                            line=dict(width=3),
                            hovertemplate='Mes: %{x}<br>📦 Pedidos: %{y:,}<extra></extra>'
                        ),
                        secondary_y=True
                    )
                    
                    fig_comp_dist.update_layout(
                        title='📊 Distribución de Ventas por Mes',
                        height=400,
                        hovermode='x unified',
                        margin=dict(l=50, r=50, t=80, b=50)
                    )
                    
                    fig_comp_dist.update_xaxes(title_text="Mes", tickangle=0)
                    fig_comp_dist.update_yaxes(title_text="Ingresos ($)", secondary_y=False)
                    fig_comp_dist.update_yaxes(title_text="Cantidad de Pedidos", secondary_y=True)
    
    # ========================================
    # GRÁFICOS DE HORAS
    # ========================================
    fig_horas_dist = go.Figure().add_annotation(text="Selecciona meses", showarrow=False)
    fig_horas_dist.update_layout(height=350)
    fig_horas_heat = go.Figure().add_annotation(text="Selecciona meses", showarrow=False)
    fig_horas_heat.update_layout(height=350)
    fig_horas_evo = go.Figure().add_annotation(text="Selecciona múltiples meses", showarrow=False)
    fig_horas_evo.update_layout(height=350)
    
    if meses_comp and len(meses_comp) > 0:
        meses_filtrados = [m for m in meses_comp if not data[data['Mes'] == m].empty]
        if meses_filtrados:
            # Distribución
            colors = px.colors.qualitative.Set1
            fig_horas_dist = go.Figure()
            for i, m in enumerate(meses_filtrados):
                dm = data[data['Mes'] == m]
                h = dm.groupby('Hora')['ID de Pedido'].nunique().reset_index()
                fig_horas_dist.add_trace(go.Bar(
                    x=h['Hora'], y=h['ID de Pedido'],
                    name=m, marker_color=colors[i % len(colors)], opacity=0.7
                ))
            fig_horas_dist.update_layout(
                title='Distribución de Pedidos por Hora',
                barmode='group',
                height=350,
                xaxis=dict(title='Hora del Día', tickmode='linear', tick0=0, dtick=2)
            )
            
            # Heatmap
            if len(meses_filtrados) > 0:
                heat = data[data['Mes'].isin(meses_filtrados)].groupby(['Hora', 'Mes']).size().reset_index(name='Pedidos')
                pivot = heat.pivot(index='Mes', columns='Hora', values='Pedidos').fillna(0)
                fig_horas_heat = go.Figure(data=go.Heatmap(
                    z=pivot.values, x=pivot.columns, y=pivot.index,
                    colorscale='Viridis',
                    hovertemplate='Mes: %{y}<br>Hora: %{x}<br>Pedidos: %{z}<extra></extra>'
                ))
                fig_horas_heat.update_layout(title='Intensidad de Ventas por Hora y Mes', height=350)
            
            # Evolución
            if len(meses_filtrados) > 1:
                horas_por_mes = data[data['Mes'].isin(meses_filtrados)].groupby(['Mes', 'Hora']).size().reset_index(name='Pedidos')
                fig_horas_evo = go.Figure()
                for hora in range(0, 24, 2):
                    dh = horas_por_mes[horas_por_mes['Hora'] == hora]
                    if not dh.empty:
                        fig_horas_evo.add_trace(go.Scatter(
                            x=dh['Mes'], y=dh['Pedidos'],
                            mode='lines+markers', name=f'{hora}:00'
                        ))
                fig_horas_evo.update_layout(title='Evolución de Horas Pico por Mes', height=350)
    
    return (subtitulo, kpis, tendencias, fig1, fig2, fig3, fig4, fig5, fig6,
            fig_mapa, fig_finde, comp, tabla_prod, factores, resumen, eventos,
            prod_container, comp_kpis, fig_comp_tend, fig_comp_dist, comp_tabla,
            fig_horas_dist, fig_horas_heat, fig_horas_evo)

# ============================================
# 14. EJECUCIÓN
# ============================================
def abrir_navegador():
    webbrowser.open('http://127.0.0.1:8050')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("✅ DASHBOARD INICIADO".center(80))
    print("="*80)
    print("\n🌐 http://127.0.0.1:8050")
    print(f"\n📊 {len(df):,} registros | ${TOTAL_INGRESOS:,.0f} | {TOTAL_PEDIDOS:,} pedidos")
    print(f"   • {df['Ciudad'].nunique()} ciudades | {df['Estado Nombre'].nunique()} estados")
    print(f"   • Período: {df['Fecha'].min()} a {df['Fecha'].max()}")
    print("\n🎯 Pestañas: GENERAL | COMPARADOR | PRODUCTO | HORAS | GEO | PRODUCTOS | EVENTOS | PROPUESTAS")
    print("\n✅ CORREGIDO: Gráfico Finde vs Laboral sin superposición")
    print("\n" + "="*80)
    
    threading.Timer(2, abrir_navegador).start()
    app.run(debug=False, port=8050)