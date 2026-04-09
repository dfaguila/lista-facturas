import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="📄 Listador de PDFs",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Listador de Documentos PDF")
st.markdown("---")

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de directorio base
    st.subheader("1. Directorio a escanear")
    base_dir = st.text_input(
        "Ruta del directorio:",
        value="",
        placeholder="Ej: C:/Documentos/FACTURA LODOS",
        help="Ingresa la ruta completa del directorio que contiene los PDFs"
    )
    
    # Opciones de escaneo
    st.subheader("2. Opciones de escaneo")
    include_subdirs = st.checkbox("Incluir subdirectorios", value=True)
    
    # Opciones de metadatos
    st.subheader("3. Información a incluir")
    show_size = st.checkbox("Tamaño del archivo", value=True)
    show_modified = st.checkbox("Fecha de modificación", value=True)
    show_created = st.checkbox("Fecha de creación", value=False)
    
    # Botón de escaneo
    st.markdown("---")
    scan_button = st.button("🔍 Escanear PDFs", type="primary", use_container_width=True)

# Función para escanear PDFs
def scan_pdfs(base_dir, include_subdirs=True):
    """Escanea el directorio buscando archivos PDF"""
    pdfs = []
    
    if not os.path.exists(base_dir):
        return None, "❌ El directorio no existe"
    
    try:
        if include_subdirs:
            # Escanear recursivamente
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        full_path = os.path.join(root, f)
                        st_info = os.stat(full_path)
                        
                        pdf_data = {
                            "Nombre PDF": f,
                            "Subcarpeta": os.path.relpath(root, base_dir),
                            "Ruta completa": full_path,
                        }
                        
                        if show_size:
                            pdf_data["Tamaño (KB)"] = round(st_info.st_size / 1024, 2)
                        
                        if show_modified:
                            pdf_data["Fecha modificación"] = datetime.fromtimestamp(
                                st_info.st_mtime
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        if show_created:
                            pdf_data["Fecha creación"] = datetime.fromtimestamp(
                                st_info.st_ctime
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        pdfs.append(pdf_data)
        else:
            # Solo directorio raíz
            for f in os.listdir(base_dir):
                if f.lower().endswith(".pdf"):
                    full_path = os.path.join(base_dir, f)
                    if os.path.isfile(full_path):
                        st_info = os.stat(full_path)
                        
                        pdf_data = {
                            "Nombre PDF": f,
                            "Ruta completa": full_path,
                        }
                        
                        if show_size:
                            pdf_data["Tamaño (KB)"] = round(st_info.st_size / 1024, 2)
                        
                        if show_modified:
                            pdf_data["Fecha modificación"] = datetime.fromtimestamp(
                                st_info.st_mtime
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        if show_created:
                            pdf_data["Fecha creación"] = datetime.fromtimestamp(
                                st_info.st_ctime
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        pdfs.append(pdf_data)
        
        return pdfs, None
    
    except Exception as e:
        return None, f"❌ Error al escanear: {str(e)}"

# Área principal
if scan_button:
    if not base_dir:
        st.warning("⚠️ Por favor ingresa un directorio válido")
    else:
        with st.spinner("🔍 Escaneando directorio..."):
            pdfs, error = scan_pdfs(base_dir, include_subdirs)
        
        if error:
            st.error(error)
        elif not pdfs:
            st.warning("⚠️ No se encontraron archivos PDF en el directorio especificado")
        else:
            # Crear DataFrame
            df = pd.DataFrame(pdfs)
            
            # Ordenar
            if include_subdirs:
                df.sort_values(by=["Subcarpeta", "Nombre PDF"], inplace=True)
            else:
                df.sort_values(by=["Nombre PDF"], inplace=True)
            
            # Guardar en session_state
            st.session_state['df_pdfs'] = df
            st.session_state['base_dir'] = base_dir
            
            st.success(f"✅ Se encontraron **{len(df)}** archivos PDF")

# Mostrar resultados si existen
if 'df_pdfs' in st.session_state:
    df = st.session_state['df_pdfs']
    base_dir = st.session_state.get('base_dir', '')
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total PDFs", len(df))
    
    with col2:
        if "Tamaño (KB)" in df.columns:
            total_size_mb = df["Tamaño (KB)"].sum() / 1024
            st.metric("💾 Tamaño total", f"{total_size_mb:.2f} MB")
    
    with col3:
        if "Subcarpeta" in df.columns:
            unique_folders = df["Subcarpeta"].nunique()
            st.metric("📁 Subcarpetas", unique_folders)
    
    with col4:
        if "Fecha modificación" in df.columns:
            latest = pd.to_datetime(df["Fecha modificación"]).max()
            st.metric("🕒 Más reciente", latest.strftime("%Y-%m-%d"))
    
    st.markdown("---")
    
    # Filtros
    st.subheader("🔍 Filtros")
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        # Filtro por nombre
        search_term = st.text_input(
            "Buscar por nombre:",
            placeholder="Ingresa texto para filtrar...",
            key="search_filter"
        )
    
    with col_filter2:
        # Filtro por subcarpeta (si aplica)
        if "Subcarpeta" in df.columns:
            subcarpetas = ["Todas"] + sorted(df["Subcarpeta"].unique().tolist())
            selected_folder = st.selectbox(
                "Filtrar por subcarpeta:",
                subcarpetas,
                key="folder_filter"
            )
    
    # Aplicar filtros
    df_filtered = df.copy()
    
    if search_term:
        df_filtered = df_filtered[
            df_filtered["Nombre PDF"].str.contains(search_term, case=False, na=False)
        ]
    
    if "Subcarpeta" in df.columns and selected_folder != "Todas":
        df_filtered = df_filtered[df_filtered["Subcarpeta"] == selected_folder]
    
    st.info(f"Mostrando **{len(df_filtered)}** de **{len(df)}** PDFs")
    
    # Mostrar tabla
    st.dataframe(
        df_filtered,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Opciones de exportación
    st.markdown("---")
    st.subheader("💾 Exportar resultados")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        # Exportar a Excel
        output_buffer = pd.io.excel.ExcelWriter("temp.xlsx", engine='openpyxl')
        df_filtered.to_excel(output_buffer, index=False, sheet_name='PDFs')
        output_buffer.close()
        
        with open("temp.xlsx", "rb") as f:
            st.download_button(
                label="📥 Descargar Excel",
                data=f,
                file_name=f"listado_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col_exp2:
        # Exportar a CSV
        csv_data = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv_data,
            file_name=f"listado_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_exp3:
        # Exportar a TXT
        txt_data = df_filtered.to_string(index=False)
        st.download_button(
            label="📥 Descargar TXT",
            data=txt_data,
            file_name=f"listado_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

else:
    # Mensaje inicial
    st.info("👈 Configura los parámetros en la barra lateral y presiona **'Escanear PDFs'** para comenzar")
    
    # Ejemplos de uso
    st.markdown("### 📝 Ejemplos de rutas:")
    st.code("Windows: C:/Users/TuUsuario/Documentos/FACTURA LODOS", language="text")
    st.code("Linux/Mac: /home/usuario/documentos/factura_lodos", language="text")
    st.code("Ruta relativa: ./documentos/facturas", language="text")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    📄 Listador de PDFs v1.0 | Desarrollado con Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
