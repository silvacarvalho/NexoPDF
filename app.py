"""
Combinar/Dividir PDF
Aplicativo web simples para combinar múltiplos PDFs em um único arquivo,
ou dividir um PDF em partes menores.
"""

import base64
import hashlib
import io
import re
import zipfile
from dataclasses import dataclass

import pymupdf
import streamlit as st
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from components.page_picker import page_picker
from components.reorder_list import reorder_list

st.set_page_config(
    page_title="Nexo PDF",
    page_icon="🔗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Estilo
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container { max-width: 760px; padding-top: 2.5rem; }
        h1 { font-weight: 700; letter-spacing: -0.02em; }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 18px; border-radius: 8px 8px 0 0;
        }
        .stButton>button { border-radius: 8px; }
        div[data-testid="stDownloadButton"] button {
            width: 100%; font-weight: 600; border-radius: 10px; padding: 0.6rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔗 Nexo PDF")
st.caption("Junte vários PDFs em um só, ou divida um PDF em partes — tudo direto no navegador.")

tab_merge, tab_split = st.tabs(["🔗 Combinar PDFs", "✂️ Dividir PDF"])


# --------------------------------------------------------------------------
# Aba: Combinar
# --------------------------------------------------------------------------
with tab_merge:
    st.subheader("Combinar vários PDFs em um único arquivo")

    uploaded = st.file_uploader(
        "Selecione ou arraste os arquivos PDF",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_uploader",
    )

    if uploaded:
        current_names = [f.name for f in uploaded]
        files_by_name = {f.name: f for f in uploaded}

        # Mantém uma ordem persistente em session_state, sincronizada com
        # o conjunto atual de arquivos enviados.
        if (
            "merge_order" not in st.session_state
            or set(st.session_state.merge_order) != set(current_names)
        ):
            st.session_state.merge_order = current_names

        # Monta os itens exibidos (nome + nº de páginas) na ordem atual.
        items = []
        for name in st.session_state.merge_order:
            try:
                files_by_name[name].seek(0)
                n_pages = len(PdfReader(files_by_name[name]).pages)
                subtitle = f"{n_pages} pág."
            except Exception:
                subtitle = "⚠️ não foi possível ler"
            items.append({"id": name, "title": name, "subtitle": subtitle, "icon": "📄"})

        st.write("**Ordem dos arquivos** (arraste para reordenar):")
        st.session_state.merge_order = reorder_list(items, key="merge_reorder")
        order = st.session_state.merge_order

        st.divider()

        output_name = st.text_input("Nome do arquivo final", value="combinado.pdf")
        if not output_name.lower().endswith(".pdf"):
            output_name += ".pdf"

        if st.button("🔗 Combinar PDFs", type="primary", use_container_width=True):
            writer = PdfWriter()
            errors = []
            for name in order:
                f = files_by_name[name]
                try:
                    f.seek(0)
                    reader = PdfReader(f)
                    for page in reader.pages:
                        writer.add_page(page)
                except PdfReadError:
                    errors.append(name)

            if errors:
                st.error(
                    "Não foi possível ler o(s) arquivo(s): " + ", ".join(errors)
                    + ". Verifique se não estão corrompidos ou protegidos por senha."
                )
            else:
                buffer = io.BytesIO()
                writer.write(buffer)
                buffer.seek(0)
                st.success(f"PDFs combinados com sucesso! Total de {len(writer.pages)} páginas.")
                st.download_button(
                    "⬇️ Baixar PDF combinado",
                    data=buffer,
                    file_name=output_name,
                    mime="application/pdf",
                    use_container_width=True,
                )
    else:
        st.info("Envie dois ou mais arquivos PDF para começar.")


# --------------------------------------------------------------------------
# Aba: Dividir
# --------------------------------------------------------------------------
@dataclass
class Range:
    start: int  # 1-based, inclusivo
    end: int    # 1-based, inclusivo


def parse_ranges(spec: str, max_pages: int) -> list[Range]:
    """Converte algo como '1-3, 5, 8-10' em uma lista de Range validados."""
    ranges = []
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    if not parts:
        raise ValueError("Informe ao menos um intervalo, ex.: 1-3, 5, 8-10")
    for part in parts:
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
        elif re.fullmatch(r"\d+", part):
            start = end = int(part)
        else:
            raise ValueError(f"Intervalo inválido: '{part}'")
        if start < 1 or end < 1 or start > end:
            raise ValueError(f"Intervalo inválido: '{part}'")
        if end > max_pages:
            raise ValueError(f"O arquivo só tem {max_pages} páginas (intervalo '{part}' inválido)")
        ranges.append(Range(start, end))
    return ranges


@st.cache_data(show_spinner="Gerando miniaturas das páginas…")
def generate_thumbnails(file_bytes: bytes, max_dim: int = 150) -> list[dict]:
    """Renderiza cada página do PDF como uma miniatura PNG (data URI)."""
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    thumbs = []
    try:
        for i, page in enumerate(doc):
            rect = page.rect
            scale = max_dim / max(rect.width, rect.height, 1)
            matrix = pymupdf.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=matrix)
            b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
            thumbs.append({
                "index": i,
                "label": f"Pág. {i + 1}",
                "thumb": f"data:image/png;base64,{b64}",
            })
    finally:
        doc.close()
    return thumbs


with tab_split:
    st.subheader("Dividir um PDF em partes")

    split_file = st.file_uploader(
        "Selecione o arquivo PDF",
        type=["pdf"],
        accept_multiple_files=False,
        key="split_uploader",
    )

    if split_file:
        file_bytes = split_file.getvalue()
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
        except PdfReadError:
            st.error("Não foi possível ler este PDF. Verifique se não está corrompido ou protegido por senha.")
            st.stop()

        base_name = re.sub(r"\.pdf$", "", split_file.name, flags=re.IGNORECASE)
        file_key = hashlib.md5(file_bytes).hexdigest()[:12]

        st.caption(f"**{split_file.name}** · {total_pages} páginas")
        if total_pages > 80:
            st.caption("⚠️ PDF com muitas páginas — gerar as miniaturas pode levar alguns segundos.")

        st.write(
            "Arraste as páginas que deseja para a caixa **Selecionadas para baixar**, "
            "na ordem que quiser. Arraste de volta para a grade (ou use o ✕) para remover."
        )

        pages = generate_thumbnails(file_bytes)
        selected_indices = page_picker(pages, key=f"page_picker_{file_key}")

        st.divider()

        n_selected = len(selected_indices)
        c1, c2 = st.columns([3, 2])
        with c1:
            st.write(f"**{n_selected} página(s) selecionada(s)**" if n_selected else "Nenhuma página selecionada ainda.")
        with c2:
            split_output_name = st.text_input(
                "Nome do arquivo",
                value=f"{base_name}_selecionadas.pdf",
                label_visibility="collapsed",
                disabled=(n_selected == 0),
            )

        if n_selected:
            if not split_output_name.lower().endswith(".pdf"):
                split_output_name += ".pdf"
            writer = PdfWriter()
            for idx in selected_indices:
                writer.add_page(reader.pages[idx])
            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            st.download_button(
                "⬇️ Baixar páginas selecionadas",
                data=buffer,
                file_name=split_output_name,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

        with st.expander("⚙️ Opções avançadas (intervalos e divisão em lote)"):
            mode = st.radio(
                "Como deseja dividir?",
                [
                    "Extrair um intervalo de páginas (gera 1 PDF)",
                    "Dividir a cada N páginas (gera vários PDFs em .zip)",
                    "Intervalos personalizados (gera vários PDFs em .zip)",
                ],
            )

            if mode.startswith("Extrair"):
                c1, c2 = st.columns(2)
                with c1:
                    start = st.number_input("Página inicial", min_value=1, max_value=total_pages, value=1)
                with c2:
                    end = st.number_input("Página final", min_value=1, max_value=total_pages, value=total_pages)

                if st.button("✂️ Extrair páginas", use_container_width=True):
                    if start > end:
                        st.error("A página inicial não pode ser maior que a final.")
                    else:
                        writer = PdfWriter()
                        for p in range(start - 1, end):
                            writer.add_page(reader.pages[p])
                        buffer = io.BytesIO()
                        writer.write(buffer)
                        buffer.seek(0)
                        out_name = f"{base_name}_p{start}-{end}.pdf"
                        st.success(f"Extraídas {end - start + 1} páginas.")
                        st.download_button(
                            "⬇️ Baixar PDF extraído",
                            data=buffer,
                            file_name=out_name,
                            mime="application/pdf",
                            use_container_width=True,
                        )

            elif mode.startswith("Dividir a cada"):
                n = st.number_input("Número de páginas por parte", min_value=1, max_value=total_pages, value=1)

                if st.button("✂️ Dividir PDF", use_container_width=True):
                    zip_buffer = io.BytesIO()
                    part = 1
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for start in range(0, total_pages, n):
                            writer = PdfWriter()
                            end = min(start + n, total_pages)
                            for p in range(start, end):
                                writer.add_page(reader.pages[p])
                            part_buffer = io.BytesIO()
                            writer.write(part_buffer)
                            zf.writestr(f"{base_name}_parte{part:02d}.pdf", part_buffer.getvalue())
                            part += 1
                    zip_buffer.seek(0)
                    st.success(f"PDF dividido em {part - 1} partes.")
                    st.download_button(
                        "⬇️ Baixar arquivos (.zip)",
                        data=zip_buffer,
                        file_name=f"{base_name}_dividido.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

            else:  # Intervalos personalizados
                spec = st.text_input(
                    "Intervalos de páginas (separados por vírgula)",
                    placeholder="ex.: 1-3, 4-6, 7",
                )
                st.caption("Cada intervalo vira um PDF separado dentro do .zip.")

                if st.button("✂️ Dividir PDF", use_container_width=True):
                    try:
                        ranges = parse_ranges(spec, total_pages)
                    except ValueError as e:
                        st.error(str(e))
                    else:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            for i, r in enumerate(ranges, start=1):
                                writer = PdfWriter()
                                for p in range(r.start - 1, r.end):
                                    writer.add_page(reader.pages[p])
                                part_buffer = io.BytesIO()
                                writer.write(part_buffer)
                                suffix = f"p{r.start}-{r.end}" if r.start != r.end else f"p{r.start}"
                                zf.writestr(f"{base_name}_{suffix}.pdf", part_buffer.getvalue())
                        zip_buffer.seek(0)
                        st.success(f"PDF dividido em {len(ranges)} partes.")
                        st.download_button(
                            "⬇️ Baixar arquivos (.zip)",
                            data=zip_buffer,
                            file_name=f"{base_name}_dividido.zip",
                            mime="application/zip",
                            use_container_width=True,
                        )
    else:
        st.info("Envie um arquivo PDF para começar.")
