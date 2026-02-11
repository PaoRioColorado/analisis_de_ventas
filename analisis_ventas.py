import pandas as pd
import os
import glob
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

print("=== INICIANDO DASHBOARD EJECUTIVO ===")

# =====================================================
# 1️⃣ CARGA DE DATOS
# =====================================================

carpeta = r"C:\Users\USUARIO\Desktop\Ciencia de Datos\Dataset de ventas"
archivos = glob.glob(os.path.join(carpeta, "*.csv"))

if not archivos:
    raise ValueError("No se encontraron archivos CSV en la carpeta")

df_list = []

for archivo in archivos:
    df_temp = pd.read_csv(archivo, encoding="utf-8-sig", low_memory=False)
    print(f"Archivo cargado: {os.path.basename(archivo)}")
    df_list.append(df_temp)

df = pd.concat(df_list, ignore_index=True)
print(f"Total filas cargadas: {len(df)}")

# =====================================================
# 2️⃣ LIMPIEZA DE DATOS (SIN INVENTAR)
# =====================================================

df = df[df["Fecha de Pedido"] != "Fecha de Pedido"]

df["Fecha de Pedido"] = pd.to_datetime(
    df["Fecha de Pedido"],
    format="%m/%d/%y %H:%M",
    errors="coerce"
)

df["Cantidad Pedida"] = pd.to_numeric(df["Cantidad Pedida"], errors="coerce")
df["Precio Unitario"] = pd.to_numeric(df["Precio Unitario"], errors="coerce")

df.dropna(subset=["Fecha de Pedido", "Cantidad Pedida", "Precio Unitario"], inplace=True)

df["Ventas"] = df["Cantidad Pedida"] * df["Precio Unitario"]

df["Mes"] = df["Fecha de Pedido"].dt.strftime("%B")

orden_meses = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]

df["Mes"] = pd.Categorical(df["Mes"], categories=orden_meses, ordered=True)

def extraer_ciudad(direccion):
    try:
        return direccion.split(",")[1].strip()
    except:
        return "Desconocida"

df["Ciudad"] = df["Dirección de Envio"].apply(extraer_ciudad)

# =====================================================
# FUNCIÓN FORMATO PROFESIONAL
# =====================================================

def formatear_monto(valor):
    if valor >= 1_000_000:
        return f"{valor/1_000_000:,.2f} millones USD"
    elif valor >= 1_000:
        return f"{valor/1_000:,.0f} mil USD"
    else:
        return f"{valor:,.0f} USD"

# =====================================================
# DASH APP
# =====================================================

app = dash.Dash(__name__)

def card(titulo, valor):
    return html.Div([
        html.H4(titulo, style={"color": "#6c757d"}),
        html.H2(valor, style={"margin": "0", "color": "#212529"})
    ], style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 4px 10px rgba(0,0,0,0.08)",
        "flex": "1",
        "textAlign": "center"
    })

app.layout = html.Div(style={
    "backgroundColor": "#f4f6f9",
    "padding": "30px",
    "fontFamily": "Segoe UI"
}, children=[

    html.H1("Dashboard Ejecutivo de Ventas 2019"),

    html.Div(id="kpis", style={
        "display": "flex",
        "gap": "20px",
        "marginBottom": "30px"
    }),

    html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "30px"}, children=[

        dcc.Dropdown(
            id="mes-filter",
            options=[{"label": m, "value": m} for m in orden_meses],
            multi=True,
            placeholder="Filtrar por Mes"
        ),

        dcc.Dropdown(
            id="ciudad-filter",
            options=[{"label": c, "value": c} for c in sorted(df["Ciudad"].unique())],
            multi=True,
            placeholder="Filtrar por Ciudad"
        ),

        dcc.Dropdown(
            id="producto-filter",
            options=[{"label": p, "value": p} for p in sorted(df["Producto"].unique())],
            multi=True,
            placeholder="Filtrar por Producto"
        ),
    ]),

    html.Div(style={
        "display": "grid",
        "gridTemplateColumns": "1fr 1fr",
        "gap": "30px"
    }, children=[
        dcc.Graph(id="ventas-mensuales"),
        dcc.Graph(id="ventas-ciudad"),
        dcc.Graph(id="top-productos"),
        dcc.Graph(id="productos-unidades"),
    ]),

    html.Br(),
    dcc.Graph(id="ventas-eventos"),

    html.Br(),
    html.Div(id="insights", style={
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 4px 10px rgba(0,0,0,0.08)"
    })
])

# =====================================================
# CALLBACK
# =====================================================

@app.callback(
    Output("kpis", "children"),
    Output("ventas-mensuales", "figure"),
    Output("ventas-ciudad", "figure"),
    Output("top-productos", "figure"),
    Output("productos-unidades", "figure"),
    Output("ventas-eventos", "figure"),
    Output("insights", "children"),
    Input("mes-filter", "value"),
    Input("ciudad-filter", "value"),
    Input("producto-filter", "value")
)
def update_dashboard(meses, ciudades, productos):

    dff = df.copy()

    if meses:
        dff = dff[dff["Mes"].isin(meses)]

    if ciudades:
        dff = dff[dff["Ciudad"].isin(ciudades)]

    if productos:
        dff = dff[dff["Producto"].isin(productos)]

    total_ventas = dff["Ventas"].sum()
    total_pedidos = dff["ID de Pedido"].nunique()
    ticket_promedio = total_ventas / total_pedidos if total_pedidos > 0 else 0

    kpis = [
        card("Total Ventas", formatear_monto(total_ventas)),
        card("Total Pedidos", f"{total_pedidos:,} pedidos"),
        card("Ticket Promedio", f"{ticket_promedio:,.2f} USD")
    ]

    ventas_mes = dff.groupby("Mes")["Ventas"].sum().reset_index()
    fig1 = px.line(ventas_mes, x="Mes", y="Ventas", title="Ventas por Mes")

    ventas_ciudad = dff.groupby("Ciudad")["Ventas"].sum().reset_index()
    fig2 = px.bar(ventas_ciudad, x="Ciudad", y="Ventas", title="Ventas por Ciudad")

    top_facturacion = dff.groupby("Producto")["Ventas"].sum().nlargest(10).reset_index()
    fig3 = px.bar(top_facturacion, x="Ventas", y="Producto",
                  orientation="h", title="Top 10 Productos por Facturación")

    top_unidades = dff.groupby("Producto")["Cantidad Pedida"].sum().nlargest(10).reset_index()
    fig4 = px.bar(top_unidades, x="Cantidad Pedida", y="Producto",
                  orientation="h", title="Top 10 Productos por Unidades Vendidas")

    # EVENTOS ESPECIALES
    eventos_dict = {"Black Friday": "11-29", "Navidad": "12-25"}
    dff["MesDia"] = dff["Fecha de Pedido"].dt.strftime("%m-%d")

    eventos_resumen = []

    for nombre, fecha in eventos_dict.items():
        df_evento = dff[dff["MesDia"] == fecha]
        if not df_evento.empty:
            eventos_resumen.append({
                "Evento": nombre,
                "Ingresos": df_evento["Ventas"].sum(),
                "Unidades": df_evento["Cantidad Pedida"].sum()
            })

    resumen_eventos = pd.DataFrame(eventos_resumen)

    if not resumen_eventos.empty:
        fig5 = px.bar(resumen_eventos, x="Evento", y="Ingresos",
                      title="Ingresos en Fechas Especiales")
    else:
        fig5 = px.bar(title="No hubo ventas en fechas especiales según filtros")

    # INSIGHTS
    insights_list = [html.H3("Insights Automáticos")]

    if total_ventas > 0:
        insights_list.append(
            html.P(f"• Ventas totales actuales: {formatear_monto(total_ventas)}.")
        )

        mejor_producto = top_facturacion.iloc[0]["Producto"] if not top_facturacion.empty else None
        if mejor_producto:
            insights_list.append(
                html.P(f"• Producto con mayor facturación: {mejor_producto}.")
            )

        for evento in eventos_resumen:
            insights_list.append(
                html.P(
                    f"• En {evento['Evento']} se vendieron "
                    f"{evento['Unidades']:,} unidades "
                    f"y se generaron {formatear_monto(evento['Ingresos'])}."
                )
            )

        insights_list.append(
            html.P("• Recomendación: reforzar stock y campañas en fechas especiales, "
                   "especialmente para los productos más vendidos.")
        )
    else:
        insights_list.append(html.P("No hay datos con los filtros seleccionados."))

    return kpis, fig1, fig2, fig3, fig4, fig5, html.Div(insights_list)

# =====================================================
# RUN
# =====================================================

print("Dashboard en http://127.0.0.1:8050/")
app.run(debug=False)
