import json
import os
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime

# Leer credenciales desde el archivo .toml
creds_dict = {
    "type": st.secrets.connections.gcs["type"],
    "project_id": st.secrets.connections.gcs["project_id"],
    "private_key_id": st.secrets.connections.gcs["private_key_id"],
    "private_key": st.secrets.connections.gcs["private_key"],
    "client_email": st.secrets.connections.gcs["client_email"],
    "client_id": st.secrets.connections.gcs["client_id"],
    "auth_uri": st.secrets.connections.gcs["auth_uri"],
    "token_uri": st.secrets.connections.gcs["token_uri"],
    "auth_provider_x509_cert_url": st.secrets.connections.gcs["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets.connections.gcs["client_x509_cert_url"]
}

# Configurar credenciales
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Abrir hoja de cálculo
try:
    spreadsheet = client.open_by_key("1TE9IPz-7T_vcWx-MbBNGZzdVGnXkggTNWAbLbx1_39Q")
    worksheet = spreadsheet.sheet1
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {str(e)}")
    st.stop()

# Contraseña predefinida (puedes cambiarla por una más segura)
PASSWORD = "ikarox"

# Función para obtener datos
def get_data():
    """Obtiene todos los registros de la hoja."""
    try:
        records = worksheet.get_all_records()  # Obtener todos los registros como diccionarios
        for record in records:
            if "UNIDADES" in record:
                record["UNIDADES"] = int(record["UNIDADES"])  # Convertir UNIDADES a entero
        return records
    except Exception as e:
        st.error(f"Error al leer datos: {str(e)}")
        return []

# Función para actualizar stock
def update_stock(row_index, new_stock):
    """Actualiza el stock en una fila específica."""
    try:
        worksheet.update_cell(row_index + 2, worksheet.find("UNIDADES").col, int(new_stock))  # +2 porque gspread usa índice base 1 y la primera fila es el encabezado
    except Exception as e:
        st.error(f"Error al actualizar stock: {str(e)}")

def log_transaction(product, operation, quantity, old_stock, new_stock, price):
    """Registra una transacción en la hoja de logs."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logs_worksheet = spreadsheet.worksheet("Logs")
        price = price * quantity if price else 0
        new_log = [timestamp, product, operation, quantity, old_stock, new_stock, price]
        logs_worksheet.append_row(new_log)
    except Exception as e:
        st.error(f"Error al registrar transacción: {str(e)}")

# Obtener datos de la hoja principal y logs
data = get_data()
logs_worksheet = spreadsheet.worksheet("Logs")
logs_data = logs_worksheet.get_all_records()

# Calcular valor de inventario actual
inventario_actual = sum(item["PRECIO DE COMPRA"] * item["UNIDADES"] for item in data)

# Calcular KPIs de ventas
ventas_tecnico = sum(log["Precio"] for log in logs_data if log["Operacion"] == "Venta técnico")
ventas_publico = sum(log["Precio"] for log in logs_data if log["Operacion"] == "Venta público")
ventas_totales = ventas_tecnico + ventas_publico

# Centrar el inventario actual con CSS personalizado y aumentar el tamaño de la fuente
st.markdown(
    """
    <style>
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        font-size: 2.5rem;  /* Aumentar el tamaño de la fuente */
        font-weight: bold;  /* Hacer el texto en negrita */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Mostrar el inventario actual centrado y con un tamaño más grande
st.markdown(
    f'<div class="centered"><h1>Valor de inventario actual: ${inventario_actual:,.2f}</h1></div>',
    unsafe_allow_html=True
)

# Mostrar KPIs con tamaño de números personalizado
st.markdown(
    """
    <style>
    .kpi-number {
        font-size: 1rem;  /* Aumentar el tamaño de los números */
        font-weight: bold;  /* Hacer los números en negrita */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div style="text-align:center;">
        <span style="display:inline-block; margin-right: 25px;">
            <strong>Ventas a público:</strong> ${ventas_publico:,.2f}
        </span>
        <span style="display:inline-block;">
            <strong>Ventas a técnicos:</strong> ${ventas_tecnico:,.2f}
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        font-size: 1rem;  /* Aumentar el tamaño de la fuente */
        font-weight: bold;  /* Hacer el texto en negrita */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Mostrar el inventario actual centrado y con un tamaño más grande
st.markdown(
    f'<div class="centered"><h1>Ventas Totales: ${ventas_totales:,.2f}</h1></div>',
    unsafe_allow_html=True
)



# Selección de producto
product_list = [item["DESCRIPCION"] for item in data]
search_term = st.selectbox("Seleccionar producto:", product_list, key="selectbox_search")

if search_term:
    selected_item = next(item for item in data if item["DESCRIPCION"] == search_term)
    desp = selected_item["DESCRIPCION"]
    st.markdown(
    """
    <style>
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        font-size: 2rem;  /* Aumentar el tamaño de la fuente */
        font-weight: bold;  /* Hacer el texto en negrita */
    }
    </style>
    """,
    unsafe_allow_html=True)

# Mostrar el inventario actual centrado y con un tamaño más grande
st.markdown(
    f'<div class="centered"><h1>${desp:,.2f}</h1></div>',
    unsafe_allow_html=True
)
    
    
    
    # Mostrar imagen del producto
    image_url = selected_item.get("URL", "")
    if image_url:
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, caption=selected_item["DESCRIPCION"], width=500)
        except Exception as e:
            st.error(f"No se pudo cargar la imagen: {str(e)}")
    else:
        st.warning("No hay imagen disponible para este producto.")
    
    # Mostrar cantidad disponible y vendida
    cantidad_disponible = selected_item["UNIDADES"]
    cantidad_vendida = sum(log["Cantidad"] for log in logs_data if log["Producto"] == selected_item["DESCRIPCION"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cantidad disponible", cantidad_disponible)
    with col2:
        st.metric("Cantidad vendida", cantidad_vendida)


    price1 = selected_item["PRECIO DE COMPRA"]
    price2 = selected_item["PRECIO DE TECNICO"]
    price3 = selected_item["PRECIO PUBLICO"]    
    
    # Mostrar KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precio de compra", price1)
    with col2:
        st.metric("Precio técnico", price2)
    with col3:
        st.metric("Precio público", price3)

# ------------------------------------------
# Sección 2: Actualización de stock (MODIFICADA)
# ------------------------------------------
st.header("🔄 Actualizar stock")
data = get_data()
product_list = [item["DESCRIPCION"] for item in data]

if product_list:
    selected_product = st.selectbox("Seleccionar producto:", product_list, key="selectbox_update")
    selected_item = next(item for item in data if item["DESCRIPCION"] == selected_product)
    current_stock = selected_item["UNIDADES"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stock actual", current_stock)
    
    with col2:
        operation = st.radio("Operación:", ["Venta al técnico", "Venta al público", "Reabastecimiento"])
    
    delta = st.number_input(
        f"Unidades a {'restar' if 'Venta' in operation else 'sumar'}:",
        min_value=0,
        key="delta"
    )
    
    password = st.text_input("Ingrese la contraseña para actualizar el stock:", type="password")
    if st.button("Actualizar stock"):
        if password == PASSWORD:
            try:
                # Determinar tipo de operación y precio
                if "Venta" in operation:
                    if "técnico" in operation:
                        operation_type = "Venta técnico"
                        price = selected_item["PRECIO DE TECNICO"]
                    else:
                        operation_type = "Venta público"
                        price = selected_item["PRECIO PUBLICO"]
                    new_stock = current_stock - delta
                else:
                    operation_type = "Reabastecimiento"
                    price = ""
                    new_stock = current_stock + delta
                
                if new_stock < 0:
                    st.error("No puedes tener stock negativo!")
                    st.stop()
                
                row_index = next(i for i, item in enumerate(data) if item["DESCRIPCION"] == selected_product)
                
                log_transaction(
                    product=selected_product,
                    operation=operation_type,
                    quantity=delta,
                    old_stock=current_stock,
                    new_stock=new_stock,
                    price=price
                )
                
                update_stock(row_index, new_stock)
                st.success(f"Stock actualizado exitosamente! Nuevo stock: {new_stock}")
                st.experimental_rerun()
            
            except Exception as e:
                st.error(f"Error al actualizar: {str(e)}")
        else:
            st.error("Contraseña incorrecta. No se puede actualizar el stock.")
else:
    st.warning("No hay productos en el inventario")

# ------------------------------------------
# Sección 3: Vista completa del inventario
# ------------------------------------------
st.header("📋 Inventario completo")
st.dataframe(get_data())
