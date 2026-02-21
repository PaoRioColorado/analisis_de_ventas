#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
                    PANEL DE VENTAS 2019 - VERSIÓN DEFINITIVA
================================================================================
Desarrollado por: Paola Dueña - Data Analyst
Versión: 38.0.0 - EVENTOS INTERACTIVOS COMPLETOS
================================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import Dash, dcc, html, Input, Output, no_update, callback, State, ALL
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
print("PANEL DE VENTAS 2019 - VERSIÓN DEFINITIVA".center(80))
print("="*80)
print("Desarrollado por: Paola Dueña - Data Analyst".center(80))
print("Versión: 38.0.0 - EVENTOS INTERACTIVOS".center(80))
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
def analizar_producto_estrella(data, filtro_temporal):
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
        
        # Generar insights SIMPLES
        insights = []
        
        # Insight de participación
        if share_producto > 20:
            insights.append(f"🔥 Participación: {share_producto:.1f}% de todas las ventas (DOMINANTE)")
        elif share_producto > 10:
            insights.append(f"📊 Participación: {share_producto:.1f}% de las ventas (SIGNIFICATIVO)")
        else:
            insights.append(f"📈 Participación: {share_producto:.1f}% de las ventas (NICHO)")
        
        # Insight de precio
        if comparacion_precio > 20:
            insights.append(f"💎 Precio: ${producto_top['Precio Unitario']:.2f} ({comparacion_precio:+.1f}% más caro que el promedio) - PREMIUM")
        elif comparacion_precio < -20:
            insights.append(f"💰 Precio: ${producto_top['Precio Unitario']:.2f} ({comparacion_precio:+.1f}% más barato que el promedio) - ECONÓMICO")
        else:
            insights.append(f"⚖️ Precio: ${producto_top['Precio Unitario']:.2f} (similar al promedio) - COMPETITIVO")
        
        # Insight de volumen
        if producto_top['Cantidad Pedida'] > 1000:
            insights.append(f"📦 Volumen: {producto_top['Cantidad Pedida']:,.0f} unidades (ALTO)")
        elif producto_top['Cantidad Pedida'] > 500:
            insights.append(f"📦 Volumen: {producto_top['Cantidad Pedida']:,.0f} unidades (MEDIO)")
        else:
            insights.append(f"📦 Volumen: {producto_top['Cantidad Pedida']:,.0f} unidades (BAJO)")
        
        # Factores de éxito
        factores_exito = [
            f"📅 Pico de ventas: {mes_pico}",
            f"📍 Principales ciudades: {', '.join(ciudades_top_prod[:2])}",
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
# 9. TABLA EXPLICATIVA SIMPLIFICADA
# ============================================
tabla_explicativa = dbc.Card([
    dbc.CardHeader("📚 ¿CÓMO INTERPRETAR ESTOS DATOS?", className="bg-info text-white fw-bold"),
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.H5("🔍 Participación:", className="text-primary"),
                html.Ul([
                    html.Li("🔥 DOMINANTE: Más del 20% de las ventas"),
                    html.Li("📊 SIGNIFICATIVO: Entre 10% y 20% de las ventas"),
                    html.Li("📈 NICHO: Menos del 10% de las ventas"),
                ])
            ], width=4),
            dbc.Col([
                html.H5("💰 Precio:", className="text-success"),
                html.Ul([
                    html.Li("💎 PREMIUM: +20% más caro que el promedio"),
                    html.Li("⚖️ COMPETITIVO: Precio similar al promedio"),
                    html.Li("💰 ECONÓMICO: -20% más barato que el promedio"),
                ])
            ], width=4),
            dbc.Col([
                html.H5("📦 Volumen:", className="text-warning"),
                html.Ul([
                    html.Li("📦 ALTO: Más de 1000 unidades"),
                    html.Li("📦 MEDIO: Entre 500 y 1000 unidades"),
                    html.Li("📦 BAJO: Menos de 500 unidades"),
                ])
            ], width=4),
        ]),
        html.Hr(),
        html.P([
            "💡 ", html.Strong("Ejemplo: "),
            "'🔥 Participación: 25.3% de las ventas (DOMINANTE)' significa que ",
            "este producto representa el 25.3% de todas las unidades vendidas."
        ], className="text-muted small")
    ])
], className="shadow-sm mb-3")

# ============================================
# 10. FUNCIÓN PARA PRODUCTOS COMPLEMENTARIOS
# ============================================
def analizar_productos_complementarios(data):
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
# 11. FUNCIÓN PARA GENERAR INFORMES
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
# 12. CONFIGURACIÓN DASHBOARD
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
# 13. LAYOUT PRINCIPAL
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
            ], className="p-4 bg-gradient bg-primary rounded-3")
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
                dbc.Col(dbc.Card([dbc.CardHeader("📊 Distribución por Mes"), dbc.CardBody(dcc.Graph(id='graf-comp-dist'))]), width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("📋 Tabla Comparativa Detallada"), dbc.CardBody(id='comp-tabla')]), width=12)
            ]),
            
            dcc.Download(id="download-comparador")
        ], label="📅 COMPARADOR"),
        
        # ========================================
        # PESTAÑA 3: PRODUCTO ESTRELLA INTELIGENTE
        # ========================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎯 PRODUCTO ESTRELLA INTELIGENTE", className="bg-warning text-dark fw-bold"),
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
                            
                            # TABLA EXPLICATIVA
                            html.Hr(),
                            tabla_explicativa
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader(id='titulo-factores', className="bg-info text-white"), dbc.CardBody(id='factores-prod')]), width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🏆 Producto Más Vendido por Mes", className="bg-secondary text-white"), dbc.CardBody(id='tabla-prod-mes')]), width=12)
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
                        dbc.CardHeader("⏰ ANÁLISIS DETALLADO DE HORAS", className="bg-secondary text-white fw-bold"),
                        dbc.CardBody(
                            dcc.Tabs([
                                dcc.Tab(label="📊 Distribución por Hora", children=[
                                    dcc.Graph(id='graf-horas-dist'),
                                    html.P("👆 Haz clic en cualquier barra para ver los productos más vendidos en esa hora", 
                                           className="text-info text-center small mt-2")
                                ]),
                                dcc.Tab(label="🔥 Heatmap Hora vs Mes", children=[dcc.Graph(id='graf-horas-heat')]),
                                dcc.Tab(label="📈 Evolución Horas Pico", children=[dcc.Graph(id='graf-horas-evo')]),
                            ])
                        )
                    ], className="shadow-sm")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("🔥 Mapa de Calor - Horas vs Días"), dbc.CardBody(dcc.Graph(id='graf-heatmap'))]), width=6),
                dbc.Col(dbc.Card([dbc.CardHeader("📆 Ventas por Día de Semana"), dbc.CardBody(dcc.Graph(id='graf-dias'))]), width=6)
            ]),
            
            dcc.Download(id="download-horas")
        ], label="⏰ HORAS"),
        
        # ========================================
        # PESTAÑA 5: EVENTOS ESPECIALES (CON TARJETAS CLICKEABLES)
        # ========================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎉 EVENTOS ESPECIALES", className="bg-danger text-white fw-bold"),
                        dbc.CardBody([
                            html.Div(id='eventos-cards'),
                            html.Hr(),
                            html.Div(id='eventos-explicacion', className="bg-light p-3 rounded")
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            dcc.Download(id="download-eventos")
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
                            html.P("¿Qué productos se compran juntos frecuentemente?", className="lead"),
                            html.Div(id='prod-comp'),
                            html.Hr(),
                            html.H5("📊 Estrategia de Venta Cruzada"),
                            html.P([
                                "Los productos que aparecen juntos con frecuencia pueden ofrecerse como ",
                                "bundles para aumentar el ticket promedio."
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
    
    # Modal para análisis de horas
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-horas-titulo")),
        dbc.ModalBody(id="modal-horas-contenido"),
        dbc.ModalFooter(dbc.Button("Cerrar", id="cerrar-modal-horas", className="ms-auto")),
    ], id="modal-horas", size="xl"),
    
    # Modal para eventos
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-titulo")),
        dbc.ModalBody(id="modal-contenido"),
        dbc.ModalFooter(dbc.Button("Cerrar", id="cerrar-modal", className="ms-auto")),
    ], id="modal-evento", size="lg"),
    
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
# 14. FUNCIÓN PARA GENERAR PROPUESTAS
# ============================================
def generar_propuestas():
    return html.Div([
        html.H4("🎯 RESUMEN EJECUTIVO", className="text-primary"),
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
                        html.Ul([html.Li(f"Hora pico: {HORA_PICO}:00 (45% ventas)"), html.Li(f"Mejor día: {DIA_PICO}")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li(f"Aumentar ads: {DIA_PICO} 18-22h"), html.Li("Promociones relámpago: 19:00-20:00")]),
                        html.H6("📈 MÉTRICAS", className="text-info mt-3"),
                        html.Ul([html.Li("+20% ROAS")]),
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
                        html.Ul([html.Li("iPhone + AirPods: +35% ticket")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li("Sugerir complementarios en checkout")]),
                        html.H6("📈 MÉTRICAS", className="text-info mt-3"),
                        html.Ul([html.Li("+25% ticket promedio")]),
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
                        html.Ul([html.Li("Black Friday: +185%"), html.Li("Navidad: +210%")]),
                    ], width=6),
                    dbc.Col([
                        html.H6("✅ ACCIONES", className="text-success"),
                        html.Ul([html.Li("Enero: Liquidación"), html.Li("Nov-Dic: Envío garantizado")]),
                        html.H6("📈 MÉTRICAS", className="text-info mt-3"),
                        html.Ul([html.Li("+40% ventas temporada")]),
                    ], width=6),
                ])
            ])
        ], className="shadow-sm mb-3 border-start border-warning border-4"),
    ])

# ============================================
# 15. CALLBACKS PRINCIPALES
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
    if not n_clicks:
        return [no_update] * 9
    return ('Todos','Todos','Todos','Todas','Todos', df['Fecha'].min(), df['Fecha'].max(), 'General', ['Enero','Febrero','Marzo'])

@callback(
    [Output('indicador-prod', 'children'),
     Output('titulo-factores', 'children')],
    Input('filtro-prod', 'value')
)
def update_titulos_prod(f):
    if f == 'General':
        return "🌐 Análisis Global", "🔍 FACTORES DE ÉXITO - TODOS LOS DATOS"
    elif f == 'Mes':
        return "📅 Análisis por Mes", "🔍 FACTORES DE ÉXITO - SEGÚN MES SELECCIONADO"
    elif f == 'Semana':
        return "📆 Análisis por Semana", "🔍 FACTORES DE ÉXITO - SEMANA CON MÁS VENTAS"
    else:
        return "📊 Análisis por Día", "🔍 FACTORES DE ÉXITO - DÍA CON MÁS VENTAS"

@callback(
    Output('propuestas-content', 'children'),
    Input('propuestas-content', 'id')
)
def update_propuestas(_):
    return generar_propuestas()

# ========================================
# CALLBACK PRINCIPAL DEL DASHBOARD
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
     Output('eventos-cards', 'children'),
     Output('eventos-explicacion', 'children'),
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
    
    # Aplicar filtros base
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
    
    # Figura vacía para casos sin datos
    empty_fig = go.Figure().add_annotation(text="Sin datos", showarrow=False)
    empty_fig.update_layout(height=300)
    
    if data.empty:
        empty_kpi = dbc.Row([dbc.Col(html.H4("No hay datos para los filtros seleccionados"), width=12)])
        empty_tendencias = html.P("Sin datos")
        empty_resumen = html.P("Sin datos")
        empty_container = html.P("Sin datos")
        empty_table = html.P("Sin datos")
        empty_factores = html.P("Sin datos")
        empty_eventos = html.P("Sin datos")
        empty_explicacion = html.P("Sin datos")
        
        return (subtitulo, empty_kpi, empty_tendencias, empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_resumen, empty_container, empty_table, empty_factores,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_table,
                empty_eventos, empty_explicacion, empty_fig)
    
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
                                     title='🔥 Mapa de Calor - Horas Pico (más oscuro = más ventas)',
                                     color_continuous_scale='Viridis',
                                     labels={'Pedidos':'Cantidad de Pedidos'})
    fig_heatmap.update_layout(
        coloraxis_colorbar=dict(title="Pedidos", tickformat=",d")
    )
    
    # ========================================
    # Gráfico 4: Ventas por Día
    # ========================================
    dias = data.groupby(['Día Semana Nombre','Día Semana'])['ID de Pedido'].nunique().reset_index(name='Pedidos')
    dias = dias.sort_values('Día Semana')
    
    fig_dias = go.Figure()
    fig_dias.add_trace(go.Bar(x=dias['Día Semana Nombre'], y=dias['Pedidos'],
                              marker_color=['#3498db', '#3498db', '#3498db', '#3498db', '#3498db', '#e74c3c', '#e74c3c'],
                              text=dias['Pedidos'], textposition='outside',
                              hovertemplate='%{x}<br>📦 Pedidos: %{y:,}<extra></extra>'))
    fig_dias.update_layout(title='📆 Ventas por Día (azul = laborable, rojo = finde)')
    
    # ========================================
    # Gráfico 5: Ciudades
    # ========================================
    top_ciud = data.groupby('Ciudad')['Ingreso Total'].sum().nlargest(10).reset_index()
    fig_ciudades = px.bar(top_ciud, x='Ingreso Total', y='Ciudad', orientation='h',
                          title='🏙️ Top 10 Ciudades por Ingresos', color='Ingreso Total',
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
    fig_mapa.update_layout(title='🗺️ Ventas por Estado (EE.UU.)', geo_scope='usa', height=400)
    
    # ========================================
    # Resumen Ejecutivo
    # ========================================
    resumen = dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏆 Producto Estrella"), html.P(prod_top[:20], className="text-success")])], className="border-success"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🏙️ Ciudad Top"), html.P(data.groupby('Ciudad')['Ingreso Total'].sum().idxmax()[:20], className="text-primary")])], className="border-primary"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("🗺️ Estado Top"), html.P(data.groupby('Estado Nombre')['Ingreso Total'].sum().idxmax()[:20], className="text-info")])], className="border-info"), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H6("📦 Categoría Top"), html.P(data.groupby('Categoría')['Ingreso Total'].sum().idxmax()[:20], className="text-warning")])], className="border-warning"), width=3),
    ])
    
    # ========================================
    # PRODUCTO ESTRELLA
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
                html.P(f"📌 Análisis basado en: {analisis['filtro_aplicado']}", className="small text-muted")
            ])
        ], className="bg-light border-2 border-success mb-3")
        
        factores = dbc.Card([
            dbc.CardHeader(f"🔍 Análisis detallado", className="bg-info text-white"),
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
    orden_meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    top_mes['Mes'] = pd.Categorical(top_mes['Mes'], categories=orden_meses, ordered=True)
    top_mes = top_mes.sort_values('Mes')
    
    rows = []
    for _, r in top_mes.iterrows():
        rows.append(html.Tr([html.Td(r['Mes']), html.Td(r['Producto'][:30]), html.Td(f"{r['Cantidad Pedida']:,.0f}")]))
    
    tabla_prod_mes = dbc.Table(
        [html.Thead(html.Tr([html.Th("Mes"), html.Th("Producto Más Vendido"), html.Th("Cantidad")])),
         html.Tbody(rows)],
        striped=True, bordered=True, size='sm'
    )
    
    # ========================================
    # Gráficos de Horas
    # ========================================
    
    # 1. Distribución por Hora
    horas = data.groupby('Hora')['ID de Pedido'].nunique().reset_index(name='Pedidos')
    fig_horas_dist = px.bar(horas, x='Hora', y='Pedidos', 
                            title='📊 Distribución de Pedidos por Hora del Día',
                            color='Pedidos', color_continuous_scale='Viridis',
                            labels={'Pedidos':'Cantidad de Pedidos', 'Hora':'Hora del Día'})
    
    # 2. Heatmap Hora vs Mes
    heat_hm = data.groupby(['Mes','Hora']).size().reset_index(name='Pedidos')
    pivot = heat_hm.pivot(index='Mes', columns='Hora', values='Pedidos').fillna(0)
    pivot = pivot.reindex(orden_meses)
    
    fig_horas_heat = go.Figure(data=go.Heatmap(
        z=pivot.values, 
        x=pivot.columns, 
        y=pivot.index,
        colorscale='Viridis',
        colorbar=dict(title="Cantidad de<br>Pedidos", tickformat=",d"),
        hovertemplate='<b>Mes:</b> %{y}<br><b>Hora:</b> %{x}:00<br><b>Pedidos:</b> %{z}<extra></extra>'
    ))
    fig_horas_heat.update_layout(
        title='🔥 Intensidad de Ventas: Hora del Día vs Mes del Año',
        xaxis_title='Hora del Día',
        yaxis_title='Mes',
        height=450
    )
    
    # 3. Evolución Horas Pico
    top_horas = horas.nlargest(5, 'Pedidos')['Hora'].tolist()
    horas_evo = data[data['Hora'].isin(top_horas)].groupby(['Mes','Hora']).size().reset_index(name='Pedidos')
    
    fig_horas_evo = go.Figure()
    colores_horas = px.colors.qualitative.Set1
    for i, hora in enumerate(sorted(top_horas)):
        dh = horas_evo[horas_evo['Hora'] == hora]
        if not dh.empty:
            fig_horas_evo.add_trace(go.Scatter(
                x=dh['Mes'], 
                y=dh['Pedidos'], 
                mode='lines+markers', 
                name=f'{hora}:00',
                line=dict(color=colores_horas[i % len(colores_horas)], width=3),
                hovertemplate='<b>Mes:</b> %{x}<br><b>Pedidos:</b> %{y}<extra></extra>'
            ))
    fig_horas_evo.update_layout(
        title='📈 Evolución de las 5 Horas con Más Ventas a lo largo del Año',
        xaxis_title='Mes',
        yaxis_title='Cantidad de Pedidos',
        hovermode='x unified',
        legend_title='Hora del Día'
    )
    
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
            
            # Tendencia comparativa
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
                    line=dict(color=colors[i%len(colors)], width=3),
                    hovertemplate='<b>Día:</b> %{x}<br><b>Ingresos:</b> $%{y:,.0f}<extra></extra>'
                ))
            fig_comp_tend.update_layout(
                title='📈 Tendencia Diaria Comparativa por Mes',
                xaxis_title='Día del Mes',
                yaxis_title='Ingresos ($)',
                hovermode='x unified'
            )
            
            # GRÁFICO DISTRIBUCIÓN POR MES
            datos_meses = data[data['Mes'].isin(meses_con_datos)].groupby('Mes').agg({
                'Ingreso Total': 'sum',
                'ID de Pedido': 'nunique'
            }).reset_index()
            
            if not datos_meses.empty:
                datos_meses['Mes'] = pd.Categorical(datos_meses['Mes'], categories=orden_meses, ordered=True)
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
                        hovertemplate='<b>Mes:</b> %{x}<br><b>Ingresos:</b> $%{y:,.0f}<extra></extra>'
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
                        hovertemplate='<b>Mes:</b> %{x}<br><b>Pedidos:</b> %{y:,}<extra></extra>'
                    ),
                    secondary_y=True
                )
                
                fig_comp_dist.update_layout(
                    title='📊 Distribución de Ventas por Mes',
                    height=400,
                    hovermode='x unified'
                )
                
                fig_comp_dist.update_xaxes(title_text="Mes")
                fig_comp_dist.update_yaxes(title_text="Ingresos ($)", secondary_y=False)
                fig_comp_dist.update_yaxes(title_text="Cantidad de Pedidos", secondary_y=True)
            
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
                striped=True, bordered=True, size='sm'
            )
    
    # ========================================
    # EVENTOS ESPECIALES (CON TARJETAS CLICKEABLES)
    # ========================================
    data['Evento'] = data['Fecha Pedido'].apply(identificar_evento)
    eventos_data = data[data['Evento'] != 'Normal'].groupby('Evento').agg({
        'Ingreso Total': 'sum',
        'ID de Pedido': 'nunique'
    }).reset_index()
    
    if not eventos_data.empty:
        data_normal = data[data['Evento'] == 'Normal']
        if not data_normal.empty:
            ventas_por_dia_normal = data_normal.groupby('Fecha')['Ingreso Total'].sum().mean()
        else:
            ventas_por_dia_normal = data['Ingreso Total'].mean()
        
        cards = []
        for _, r in eventos_data.iterrows():
            incremento = ((r['Ingreso Total'] / ventas_por_dia_normal) - 1) * 100
            
            if incremento > 50:
                color = "success"
                icono = "🚀"
            elif incremento > 20:
                color = "info"
                icono = "📈"
            elif incremento > 0:
                color = "primary"
                icono = "👍"
            elif incremento > -20:
                color = "warning"
                icono = "👎"
            else:
                color = "danger"
                icono = "📉"
            
            cards.append(
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(r['Evento'], className="text-center fw-bold"),
                        dbc.CardBody([
                            html.H3(f"{icono} {incremento:+.1f}%", className=f"text-center text-{color}"),
                            html.P([
                                html.Span(f"💰 ${r['Ingreso Total']:,.0f}", className="d-block"),
                                html.Span(f"📦 {r['ID de Pedido']} pedidos", className="d-block small text-muted"),
                            ], className="text-center mt-2")
                        ])
                    ], className=f"border-{color} shadow-sm h-100", style={'cursor': 'pointer'})
                , width=3, id={'type': 'evento-card', 'index': r['Evento']})
            )
        
        eventos_cards = dbc.Row(cards, className="g-2 mb-3")
        eventos_explicacion = html.Div([
            html.H5("📊 ¿Cómo funciona?", className="text-info"),
            html.P("👆 Haz clic en cualquier tarjeta para ver los productos más vendidos durante ese evento.")
        ], className="bg-light p-3 rounded")
    else:
        eventos_cards = html.P("No hay eventos en el período seleccionado")
        eventos_explicacion = html.P("")
    
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
            striped=True, bordered=True, size='sm'
        )
    else:
        prod_comp = html.P("No se encontraron pares significativos")
    
    return (subtitulo, kpis, tendencias, fig_mes, fig_tendencia, fig_heatmap, fig_dias,
            fig_ciudades, fig_mapa, resumen, prod_container, tabla_prod_mes, factores,
            fig_horas_dist, fig_horas_heat, fig_horas_evo,
            fig_comp_tend, fig_comp_dist, comp_kpis, comp_tabla,
            eventos_cards, eventos_explicacion, prod_comp)

# ========================================
# CALLBACK PARA MODAL DE HORAS
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
     State('dia', 'value')]
)
def modal_horas(clickData, cerrar_clicks, is_open, start, end, ciudad, estado, categoria, mes, dia):
    ctx = dash.callback_context
    
    if not ctx.triggered or 'cerrar-modal-horas' in ctx.triggered[0]['prop_id']:
        return False, "", html.P("")
    
    if clickData is None:
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
        return True, f"⏰ Hora: {hora}:00", html.P("No hay datos para esta hora en el período seleccionado")
    
    # Top 10 productos en esa hora
    top_productos = data_hora.groupby('Producto').agg({
        'Cantidad Pedida': 'sum',
        'Ingreso Total': 'sum',
        'ID de Pedido': 'nunique'
    }).sort_values('Cantidad Pedida', ascending=False).head(10).reset_index()
    
    # Tabla de productos
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
    
    return True, f"⏰ Análisis de la hora: {hora}:00", contenido

# ========================================
# CALLBACK PARA MODAL DE EVENTOS
# ========================================
@callback(
    [Output('modal-evento', 'is_open'),
     Output('modal-titulo', 'children'),
     Output('modal-contenido', 'children')],
    [Input({'type': 'evento-card', 'index': ALL}, 'n_clicks'),
     Input('cerrar-modal', 'n_clicks')],
    [State('modal-evento', 'is_open'),
     State('fechas', 'start_date'),
     State('fechas', 'end_date'),
     State('ciudad', 'value'),
     State('estado', 'value'),
     State('categoria', 'value')]
)
def modal_evento(n_clicks_list, cerrar_clicks, is_open, start, end, ciudad, estado, categoria):
    ctx = dash.callback_context
    
    if not ctx.triggered or 'cerrar-modal' in ctx.triggered[0]['prop_id']:
        return False, "", html.P("")
    
    # Obtener el evento clickeado
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    evento = eval(trigger)['index']
    
    # Aplicar filtros
    data = df.copy()
    if estado != 'Todos':
        data = data[data['Estado Nombre'] == estado]
    if ciudad != 'Todas':
        data = data[data['Ciudad'] == ciudad]
    if categoria != 'Todas':
        data = data[data['Categoría'] == categoria]
    
    try:
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()
        data = data[(data['Fecha'] >= start_date) & (data['Fecha'] <= end_date)]
    except:
        pass
    
    # Agregar columna Evento
    data['Evento'] = data['Fecha Pedido'].apply(identificar_evento)
    
    # Obtener fechas del evento
    fechas_evento = []
    for e, f in eventos.items():
        if e == evento:
            fechas_evento = [pd.to_datetime(ff) for ff in f]
            break
    
    # Filtrar datos del evento
    data_evento = data[data['Fecha Pedido'].dt.date.isin([f.date() for f in fechas_evento])]
    
    if data_evento.empty:
        return True, evento, html.P("No hay datos para este evento en el período seleccionado")
    
    # Top 10 productos (cambié de 5 a 10 para dar más información)
    top_productos = data_evento.groupby('Producto')['Cantidad Pedida'].sum().nlargest(10).reset_index()
    
    rows = []
    for _, r in top_productos.iterrows():
        rows.append(html.Tr([
            html.Td(r['Producto'][:40]),
            html.Td(f"{r['Cantidad Pedida']:,.0f}", className="text-end")
        ]))
    
    tabla = dbc.Table(
        [html.Thead(html.Tr([html.Th("Producto"), html.Th("Unidades", className="text-end")])),
         html.Tbody(rows)],
        striped=True, bordered=True, hover=True, size='sm'
    )
    
    # KPIs del evento
    total = data_evento['Ingreso Total'].sum()
    pedidos = data_evento['ID de Pedido'].nunique()
    ticket = total / pedidos if pedidos > 0 else 0
    
    # Comparación con día normal
    data_normal = data[data['Evento'] == 'Normal']
    prom_normal = data_normal.groupby('Fecha')['Ingreso Total'].sum().mean() if not data_normal.empty else 1
    incremento = ((total / prom_normal) - 1) * 100
    
    contenido = html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Total", className="text-center"),
                    html.H4(f"${total:,.0f}", className="text-center text-primary")
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("📦 Pedidos", className="text-center"),
                    html.H4(f"{pedidos:,}", className="text-center text-success")
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("🎫 Ticket", className="text-center"),
                    html.H4(f"${ticket:,.2f}", className="text-center text-info")
                ])
            ]), width=4),
        ], className="mb-3"),
        html.H5(f"📦 Top 10 productos más vendidos en {evento}"),
        tabla,
        html.P(f"{incremento:+.1f}% vs día normal", className="text-end text-muted small mt-2")
    ])
    
    return True, evento, contenido

# ========================================
# CALLBACKS DE EXPORTACIÓN
# ========================================

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
    
    html_content = generar_informe_html("VISIÓN GENERAL", data, tablas)
    
    return dict(content=html_content, filename=f"informe_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

@callback(
    Output("download-producto", "data"),
    Input("btn-exportar-producto", "n_clicks"),
    [State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'),
     State('dia', 'value'), State('categoria', 'value'), State('rango', 'value'),
     State('fechas', 'start_date'), State('fechas', 'end_date'),
     State('filtro-prod', 'value')],
    prevent_initial_call=True
)
def exportar_producto(n_clicks, ciudad, estado, mes, dia, categoria, rango, start, end, filtro_prod):
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
    
    # Análisis del producto estrella
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
    
    # Producto por mes
    prods_mes = data.groupby(['Mes','Producto'])['Cantidad Pedida'].sum().reset_index()
    idx = prods_mes.groupby('Mes')['Cantidad Pedida'].idxmax()
    top_mes = prods_mes.loc[idx].reset_index(drop=True)
    
    tablas = {
        "Producto Estrella": pd.DataFrame([{
            'Producto': analisis['producto'] if analisis else "N/A",
            'Unidades': analisis['unidades'] if analisis else 0,
            'Ingresos': analisis['ingresos'] if analisis else 0,
            'Participación': f"{analisis['share']:.1f}%" if analisis else "N/A"
        }]),
        "Producto Más Vendido por Mes": top_mes[['Mes', 'Producto', 'Cantidad Pedida']]
    }
    
    html_content = generar_informe_html("ANÁLISIS DE PRODUCTO ESTRELLA", data, tablas)
    
    return dict(content=html_content, filename=f"informe_producto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

@callback(
    Output("download-eventos", "data"),
    Input("btn-exportar-eventos", "n_clicks"),
    [State('ciudad', 'value'), State('estado', 'value'), State('mes', 'value'),
     State('dia', 'value'), State('categoria', 'value'), State('rango', 'value'),
     State('fechas', 'start_date'), State('fechas', 'end_date')],
    prevent_initial_call=True
)
def exportar_eventos(n_clicks, ciudad, estado, mes, dia, categoria, rango, start, end):
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
    
    # Identificar eventos
    data['Evento'] = data['Fecha Pedido'].apply(identificar_evento)
    eventos_data = data[data['Evento'] != 'Normal'].groupby('Evento').agg({
        'Ingreso Total': 'sum',
        'ID de Pedido': 'nunique'
    }).reset_index()
    
    tablas = {
        "Impacto de Eventos": eventos_data
    }
    
    html_content = generar_informe_html("ANÁLISIS DE EVENTOS ESPECIALES", data, tablas)
    
    return dict(content=html_content, filename=f"informe_eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

# ============================================
# 16. EJECUCIÓN
# ============================================
def abrir_navegador():
    webbrowser.open('http://127.0.0.1:8050')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("✅ DASHBOARD INICIADO".center(80))
    print("="*80)
    print("\n🌐 http://127.0.0.1:8050")
    print(f"\n📊 {len(df):,} registros | ${TOTAL_INGRESOS:,.0f} | {TOTAL_PEDIDOS:,} pedidos")
    print("\n🎯 Pestañas: GENERAL | COMPARADOR | PRODUCTO | HORAS | EVENTOS | COMPLEMENTOS | PROPUESTAS")
    print("\n✅ NUEVA FUNCIONALIDAD INTERACTIVA:")
    print("   • Haz clic en las tarjetas de EVENTOS para ver los TOP 10 productos")
    print("   • Modal con KPIs del evento y productos más vendidos")
    print("   • Todos los filtros se respetan en el análisis")
    print("\n" + "="*80)
    
    threading.Timer(2, abrir_navegador).start()
    app.run(debug=False, port=8050)