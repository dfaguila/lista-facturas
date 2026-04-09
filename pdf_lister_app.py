import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import io

st.set_page_config(
    page_title="📄 Listador de PDFs",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Listador de Documentos PDF")
st.markdown("---")

# Tabs para diferentes modos
tab1, tab2 = st.tabs(["📁 Escanear Carpeta Local", "📤 Subir PDFs"])

# ============================================================
# TAB 1: ESCANEAR CARPETA LOCAL
# ============================================================
with tab1:
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Selector de directorio base
        st.subheader("1. Directorio a escanear")
        
        # Opción de método
        input_method = st.radio(
            "Método de selección:",
            ["📝 Ingresar ruta manualmente", "📂 Directorio actual"],
            help="Elige cómo especificar el directorio"
        )
        
        if input_method == "📝 Ingresar ruta manualmente":
            base_dir = st.text_input(
                "Ruta del directorio:",
                value="",
                placeholder="Ej: C:/Users/daguilag/Downloads/FACTURAS",
                help="Pega la ruta completa del directorio"
            )
            
            # Botón de ayuda
            with st.expander("❓ ¿Cómo copiar la ruta?"):
                st.markdown("""
                **Windows:**
                1. Abre el Explorador de archivos
                2. Navega a tu carpeta
                3. Clic en la barra de direcciones
                4. Ctrl+C para copiar
                5. Pega aquí
                
                **Nota:** Usa `/` o `\\` como separador
                """)
        else:
            # Usar directorio donde se ejecuta la app
            current_dir = os.getcwd()
            st.info(f"📂 `{current_dir}`")
            
            # Listar subdirectorios
            try:
                subdirs = ["."] + sorted([d for d in os.listdir(current_dir) 
                                         if os.path.isdir(os.path.join(current_dir, d)) 
                                         and not d.startswith('.')])
                selected_subdir = st.selectbox("Subcarpeta:", subdirs)
                
                if selected_subdir == ".":
                    base_dir = current_dir
                else:
                    base_dir = os.path.join(current_dir, selected_subdir)
            except:
                base_dir = current_dir
        
        # Opciones de escaneo
        st.subheader("2. Opciones")
        include_subdirs = st.checkbox("Incluir subdirectorios", value=True)
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
            return None, f"❌ El directorio no existe: {base_dir}"
        
        try:
            if include_subdirs:
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
                st.info("💡 **Sugerencia:** Copia la ruta completa desde el Explorador de archivos")
            elif not pdfs:
                st.warning("⚠️ No se encontraron archivos PDF en el directorio especificado")
            else:
                df = pd.DataFrame(pdfs)
                
                if include_subdirs and "Subcarpeta" in df.columns:
                    df.sort_values(by=["Subcarpeta", "Nombre PDF"], inplace=True)
                else:
                    df.sort_values(by=["Nombre PDF"], inplace=True)
                
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
            search_term = st.text_input(
                "Buscar por nombre:",
                placeholder="Ingresa texto...",
                key="search_filter"
            )
        
        with col_filter2:
            if "Subcarpeta" in df.columns:
                subcarpetas = ["Todas"] + sorted(df["Subcarpeta"].unique().tolist())
                selected_folder = st.selectbox("Filtrar por subcarpeta:", subcarpetas)
        
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
        st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
        
        # Exportación
        st.markdown("---")
        st.subheader("💾 Exportar resultados")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='PDFs')
            
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"listado_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_exp2:
            csv_data = df_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv_data,
                file_name=f"listado_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp3:
            txt_data = df_filtered.to_string(index=False)
            st.download_button(
                label="📥 Descargar TXT",
                data=txt_data,
                file_name=f"listado_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("👈 Configura la ruta en la barra lateral y presiona **'Escanear PDFs'**")

# ============================================================
# TAB 2: SUBIR PDFs DIRECTAMENTE
# ============================================================
with tab2:
    st.info("📤 Sube tus archivos PDF directamente desde tu computador")
    
    uploaded_files = st.file_uploader(
        "Selecciona archivos PDF",
        type=['pdf'],
        accept_multiple_files=True,
        help="Puedes seleccionar múltiples archivos a la vez"
    )
    
    if uploaded_files:
        pdfs_uploaded = []
        
        for uploaded_file in uploaded_files:
            pdf_data = {
                "Nombre PDF": uploaded_file.name,
                "Tamaño (KB)": round(uploaded_file.size / 1024, 2),
                "Tamaño (MB)": round(uploaded_file.size / (1024 * 1024), 3),
            }
            pdfs_uploaded.append(pdf_data)
        
        df_uploaded = pd.DataFrame(pdfs_uploaded)
        df_uploaded.sort_values(by=["Nombre PDF"], inplace=True)
        
        st.success(f"✅ {len(df_uploaded)} archivo(s) subido(s)")
        
        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total archivos", len(df_uploaded))
        with col2:
            total_mb = df_uploaded["Tamaño (MB)"].sum()
            st.metric("💾 Tamaño total", f"{total_mb:.2f} MB")
        
        # Mostrar tabla
        st.dataframe(df_uploaded, use_container_width=True, hide_index=True)
        
        # Exportar
        st.markdown("---")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_uploaded.to_excel(writer, index=False, sheet_name='PDFs')
            
            st.download_button(
                label="📥 Descargar Listado Excel",
                data=buffer.getvalue(),
                file_name=f"listado_pdfs_subidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_exp2:
            csv_data = df_uploaded.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar Listado CSV",
                data=csv_data,
                file_name=f"listado_pdfs_subidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    📄 Listador de PDFs v2.0 | Modo dual: Escaneo local + Carga directa
    </div>
    """,
    unsafe_allow_html=True
)
