import tkinter as tk
from tkinter import ttk, filedialog
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime, timedelta
import cv2
import pytesseract
from PIL import Image

# Configurar la ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Definir las fechas de halving
halving_dates = [
    datetime(2012, 11, 28),
    datetime(2016, 7, 9),
    datetime(2020, 5, 11)
]

# Definir niveles de soporte y resistencia (ejemplo)
support_levels = [30000, 25000, 20000]
resistance_levels = [40000, 45000, 50000]

def get_data_binance(interval='1d'):
    fecha_inicio = datetime.now() - timedelta(days=365)  # Obtener datos del último año
    fecha_fin = datetime.now()
    dias = (fecha_fin - fecha_inicio).days

    klines = []
    while dias > 0:
        limit = min(dias, 1000)
        url = f'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&startTime={int(fecha_inicio.timestamp() * 1000)}&limit={limit}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            klines.extend(data)
            fecha_inicio = datetime.fromtimestamp(data[-1][0] / 1000)
        else:
            print(f"Error en la solicitud de Binance: {response.status_code}")
            break
        dias = (fecha_fin - fecha_inicio).days

    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'number_of_trades', 
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    df = df.astype(float)
    
    return df

def get_realtime_data():
    url = 'https://api.binance.com/api/v3/ticker/price'
    params = {'symbol': 'BTCUSDT'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return float(data['price'])
    else:
        print(f"Error en la solicitud de precio en tiempo real: {response.status_code}")
        return None

def update_data():
    global btc_data
    realtime_price = get_realtime_data()
    if realtime_price is not None:
        new_row = pd.DataFrame({
            'open': [realtime_price],
            'high': [realtime_price],
            'low': [realtime_price],
            'close': [realtime_price],
            'volume': [0.0],
        }, index=[datetime.now()])
        btc_data = pd.concat([btc_data, new_row])
        btc_data['SMA_20'] = btc_data['close'].rolling(window=20).mean()
        btc_data['SMA_50'] = btc_data['close'].rolling(window=50).mean()
        btc_data.dropna(inplace=True)
    else:
        print("No se pudo actualizar el precio en tiempo real")
    return btc_data

def plot_realtime_close_prices(data):
    plt.figure(figsize=(14, 7))
    plt.plot(data.index, data['close'], label='Precio de Cierre')

    # Añadir líneas verticales para los halvings
    for date in halving_dates:
        plt.axvline(x=date, color='red', linestyle='--', label='Halving')

    # Añadir líneas horizontales para soporte y resistencia
    for level in support_levels:
        plt.axhline(y=level, color='green', linestyle='--', label='Soporte')
    for level in resistance_levels:
        plt.axhline(y=level, color='blue', linestyle='--', label='Resistencia')

    plt.title('Precio de Cierre del Bitcoin en Tiempo Real')
    plt.xlabel('Fecha')
    plt.ylabel('Precio (USD)')
    plt.legend(loc='upper left', frameon=False)  # Eliminar el fondo de la leyenda
    return plt.gcf()

def display_graph(fig, tab):
    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    toolbar = NavigationToolbar2Tk(canvas, tab)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def update_plot():
    update_data()
    fig = plot_realtime_close_prices(btc_data)
    display_graph(fig, tab1)
    root.after(10000, update_plot)  # Actualizar cada 10 segundos (10000 milisegundos)

def on_interval_change(event):
    global btc_data
    interval = interval_var.get()
    btc_data = get_data_binance(interval)
    fig = plot_realtime_close_prices(btc_data)
    display_graph(fig, tab1)

def load_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        analyze_image(file_path)

def analyze_image(file_path):
    try:
        # Usar PIL para abrir la imagen
        image = Image.open(file_path)
        # Usar OCR para extraer texto de la imagen
        text = pytesseract.image_to_string(image)
        print("Texto extraído de la imagen:", text)
        # Aquí puedes agregar el análisis de IA basado en el texto extraído
    except Exception as e:
        print(f"Error al analizar la imagen: {e}")

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Predicción del Precio del Bitcoin en Tiempo Real")
root.geometry("1200x800")

# Crear un Notebook para las pestañas
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Crear las pestañas
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text='Gráfico en Tiempo Real')
notebook.add(tab2, text='Análisis de Imagen')

# Frame para los gráficos en la primera pestaña
frame1 = ttk.Frame(tab1)
frame1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Frame para los botones en la parte superior izquierda de la primera pestaña
button_frame1 = ttk.Frame(tab1)
button_frame1.pack(side=tk.TOP, anchor='nw')

# Menú desplegable para seleccionar el intervalo de tiempo
interval_var = tk.StringVar(value='1d')
interval_menu = ttk.Combobox(button_frame1, textvariable=interval_var, values=['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M'])
interval_menu.pack(side=tk.LEFT)
interval_menu.bind('<<ComboboxSelected>>', on_interval_change)

# Botón para cargar imágenes al lado del menú desplegable
load_image_button = ttk.Button(button_frame1, text="Cargar Imagen", command=load_image)
load_image_button.pack(side=tk.LEFT)

# Inicializar btc_data con un DataFrame vacío
btc_data = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

# Mostrar gráfico inicial en la primera pestaña
fig = plot_realtime_close_prices(btc_data)
display_graph(fig, tab1)

# Iniciar la actualización del gráfico
root.after(10000, update_plot)  # Actualizar cada 10 segundos (10000 milisegundos)

root.mainloop()
