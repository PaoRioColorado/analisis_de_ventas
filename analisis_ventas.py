import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import tkinter as tk
from tkinter import ttk
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# =========================
# CARGA, LIMPIEZA Y PREPARACIÓN
# =========================

def cargar_datos():
    carpeta = r"C:\Users\paola\Desktop\Ciencia de Datos\ventas"
    archivos = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith(".csv")]

    lista_df = []

    for archivo in archivos:
        df = pd.read_csv(archivo)

        # Limpiar columnas
        df.columns = df.columns.str.strip()
        df.dropna(how="all", inplace=True)

        # Eliminar encabezados repetidos
        if "Cantidad Pedida" in df.columns:
            df = df[df["Cantidad Pedida"] != "Cantidad Pedida"]

        # Conversión de tipos
        if "Cantidad Pedida" in df.columns:
            df["Cantidad Pedida"] = pd.to_numeric(df["Cantidad Pedida"], errors="coerce")

        if "Precio Unitario" in df.columns:
            df["Precio Unitario"] = pd.to_numeric(df["Precio Unitario"], errors="coerce")

        if "Fecha de Pedido" in df.columns:
            df["Fecha de Pedido"] = pd.to_datetime(
                df["Fecha de Pedido"],
                format="%m/%d/%y %H:%M",
                errors="coerce"
            )

        # Eliminar filas inválidas
        df.dropna(subset=["Cantidad Pedida", "Precio Unitario", "Fecha de Pedido"], inplace=True)

        lista_df.append(df)

    # Unir todos los CSV
    if lista_df:
        ventas = pd.concat(lista_df, ignore_index=True)
    else:
        ventas = pd.DataFrame()

    # Variables derivadas
    if not ventas.empty:
        ventas["Ventas USD"] = ventas["Cantidad Pedida"] * ventas["Precio Unitario"]
        ventas["Hora"] = ventas["Fecha de Pedido"].dt.hour
        ventas["Mes"] = ventas["Fecha de Pedido"].dt.month
        ventas["DiaSemana"] = ventas["Fecha de Pedido"].dt.day_name()
        ventas["EsFinDeSemana"] = ventas["DiaSemana"].isin(["Saturday", "Sunday"])

    return ventas

ventas = cargar_datos()

print("Filas cargadas:", ventas.shape)
print("Columnas:", ventas.columns.tolist())
print(ventas.head())

# =========================
# FORMATO
# =========================

def formato_usd(x, pos):
    return f"${x:,.0f} USD"

# =========================
# GRÁFICOS
# =========================

def grafico_ingresos_por_mes():
    if ventas.empty:
        print("No hay datos para graficar.")
        return
    datos = ventas.groupby("Mes")["Ventas USD"].sum()
    plt.figure(figsize=(10, 5))
    plt.plot(datos.index, datos.values, marker="o")
    plt.title("Ingresos Mensuales (USD)")
    plt.xlabel("Mes")
    plt.ylabel("Ingresos")
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(formato_usd))
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

def grafico_ingresos_por_hora():
    if ventas.empty:
        print("No hay datos para graficar.")
        return
    datos = ventas.groupby("Hora")["Ventas USD"].sum()
    plt.figure(figsize=(10, 5))
    plt.bar(datos.index, datos.values)
    plt.title("Ingresos por Hora del Día (USD)")
    plt.xlabel("Hora")
    plt.ylabel("Ingresos")
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(formato_usd))
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()

def grafico_heatmap_hora_mes():
    if ventas.empty:
        print("No hay datos para graficar.")
        return
    pivot = ventas.pivot_table(index="Hora", columns="Mes", values="Ventas USD", aggfunc="sum")
    plt.figure(figsize=(12,6))
    sns.heatmap(pivot, cmap="YlGnBu", annot=False)
    plt.title("Ventas por Hora y Mes (USD)")
    plt.tight_layout()
    plt.show()

def grafico_producto_mas_vendido():
    if ventas.empty:
        print("No hay datos para graficar.")
        return
    datos = ventas.groupby("Producto")["Cantidad Pedida"].sum().sort_values(ascending=False).head(10)
    plt.figure(figsize=(10, 6))
    datos.plot(kind="barh")
    plt.title("Top 10 Productos Más Vendidos")
    plt.xlabel("Unidades")
    plt.gca().invert_yaxis()
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.show()

# =========================
# DASHBOARD TKINTER
# =========================

root = tk.Tk()
root.title("Dashboard de Ventas")
root.geometry("450x500")

titulo = tk.Label(root, text="Dashboard de Ventas (USD)", font=("Segoe UI", 16, "bold"))
titulo.pack(pady=15)

style = ttk.Style()
style.configure("TButton", padding=8)

ttk.Button(root, text="Ingresos por Mes", command=grafico_ingresos_por_mes).pack(pady=5)
ttk.Button(root, text="Ingresos por Hora", command=grafico_ingresos_por_hora).pack(pady=5)
ttk.Button(root, text="Heatmap Hora-Mes", command=grafico_heatmap_hora_mes).pack(pady=5)
ttk.Button(root, text="Top Productos", command=grafico_producto_mas_vendido).pack(pady=5)

root.mainloop()
