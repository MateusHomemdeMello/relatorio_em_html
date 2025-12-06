import streamlit as st
import base64
import json
import html as html_std

# ============================================================
# ESTADO GLOBAL
# ============================================================

def init_state():
    if "blocks" not in st.session_state:
        st.session_state["blocks"] = []
    if "edit_index" not in st.session_state:
        st.session_state["edit_index"] = None
    if "edit_data" not in st.session_state:
        st.session_state["edit_data"] = None


# ============================================================
# UTILITÁRIOS
# ============================================================

def image_to_base64(file):
    bytes_data = file.read()
    b64 = base64.b64encode(bytes_data).decode("utf-8")
    return f"data:{file.type};base64,{b64}"


def load_html_file(upload):
    return upload.read().decode("utf-8")


# ============================================================
# GERADOR DE HTML FINAL
# ============================================================

def build_html(blocks, page_title="Diagnóstico de Área"):
    css = """
    <style>
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #f5f5f5;
    }

    .page {
        max-width: 1200px;
        margin: 25px auto;
        background: #ffffff;
        padding: 30px 50px;
        border-radius: 12px;
        box-shadow: 0 0 18px rgba(0,0,0,0.15);
    }

    .title { font-size: 28px; font-weight: 700; margin-bottom: 5px; }
    .subtitle { color: #666; margin-bottom: 25px; }

    .section-title {
        font-size: 20px;
        font-weight: 600;
        margin-top: 32px;
        margin-bottom: 10px;
        border-left: 4px solid #0066cc;
        padding-left: 8px;
    }

    .text-block {
        font-size: 15px;
        line-height: 1.6;
        margin-bottom: 10px;
    }

    .box-block {
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 0;
        background: #f9fafc;
        font-size: 14px;
    }

    .divider-block {
        border: none;
        border-top: 1px solid #cccccc;
        margin: 24px 0 16px 0;
    }

    .image-block {
        text-align: center;
        margin: 20px 0;
    }

    .image-block img {
        border-radius: 8px;
        box-shadow: 0 0 8px rgba(0,0,0,0.1);
    }

    .html-block {
        margin: 25px 0;
        background: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.12);
    }

    .html-block-title {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 10px;
        color: #333333;
        border-bottom: 1px solid #dddddd;
        padding-bottom: 6px;
    }

    .html-content {
        border-radius: 8px;
        overflow: hidden;
        position: relative;
    }

    /* Estes estilos só afetariam Leaflet se não usássemos iframe.
       Mantidos aqui, mas dentro do iframe (srcdoc) é outro DOM. */

    .footer {
        text-align: center;
        margin: 30px 0 10px 0;
        color: #777;
        font-size: 12px;
    }
    </style>
    """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>{page_title}</title>
        {css}
    </head>
    <body>
    <div class="page">
    """

    for block in blocks:
        t = block["type"]

        raw_width = block.get("width") or 0
        raw_height = block.get("height") or 0

        # largura: se 0 -> ocupar 100%
        if raw_width > 0:
            width_css = f"{raw_width}px"
        else:
            width_css = "100%"

        # altura: se 0 -> padrão 600 px para blocos que precisam
        height_css = f"{raw_height}px" if raw_height > 0 else "auto"

        style_size = f"width:{width_css}; height:{height_css};"

        if t == "title":
            html += f"""
            <div class="title">{block['text']}</div>
            <div class="subtitle">{block['subtitle']}</div>
            """

        elif t == "section":
            html += f"""<div class="section-title">{block['text']}</div>"""

        elif t == "text":
            style = f"font-size:{block['font_size']}px; text-align:{block['align']};"
            if block["bold"]:
                style += " font-weight:700;"
            if block["italic"]:
                style += " font-style:italic;"
            html += f"""
            <div class="text-block" style="{style}">
                {block['text']}
            </div>
            """

        elif t == "box":
            html += f"""<div class="box-block">{block['text']}</div>"""

        elif t == "divider":
            html += """<hr class="divider-block"/>"""

        elif t == "image":
            html += f"""
            <div class="image-block" style="{style_size}">
                <img src="{block['src']}" style="{style_size}" />
                {f"<div style='font-size:12px;color:#666;margin-top:4px;'>{block['caption']}</div>" if block.get('caption') else ""}
            </div>
            """

        elif t == "html":
            # altura do iframe: se não houver, usa 600 px
            iframe_height = raw_height if raw_height > 0 else 600

            # escapa o HTML original para uso em srcdoc
            escaped_html = html_std.escape(block["html"], quote=True)

            html += f"""
            <div class="html-block">
                {f'<div class="html-block-title">{block["title"]}</div>' if block.get("title") else ""}
                <div class="html-content" style="width:{width_css}; height:{iframe_height}px;">
                    <iframe
                        srcdoc='{escaped_html}'
                        style="width:100%; height:100%; border:none;"
                        title="{html_std.escape(block.get('title') or 'Mapa interativo', quote=True)}">
                    </iframe>
                </div>
            </div>
            """

    html += """
    </div>
    <div class="footer">
        Relatório Interativo • Gerado automaticamente
    </div>
    </body>
    </html>
    """

    return html


# ============================================================
# EDITOR DE BLOCOS (MODAL)
# ============================================================

def edit_block(index, block):
    st.sidebar.markdown("### ✏️ Editar bloco")

    t = block["type"]

    width = st.sidebar.number_input("Largura (px)", min_value=0, value=block.get("width", 0))
    height = st.sidebar.number_input("Altura (px)", min_value=0, value=block.get("height", 0))

    if t == "title":
        title = st.sidebar.text_input("Título", block["text"])
        subtitle = st.sidebar.text_input("Subtítulo", block["subtitle"])
        if st.sidebar.button("Salvar"):
            st.session_state["blocks"][index] = {
                "type": "title",
                "text": title,
                "subtitle": subtitle,
                "width": width,
                "height": height
            }
            st.session_state["edit_index"] = None
            st.experimental_rerun()

    elif t == "section":
        text = st.sidebar.text_input("Nome da seção", block["text"])
        if st.sidebar.button("Salvar"):
            st.session_state["blocks"][index] = {
                "type": "section",
                "text": text,
                "width": width,
                "height": height
            }
            st.session_state["edit_index"] = None
            st.experimental_rerun()

    elif t == "text":
        text = st.sidebar.text_area("Texto", block["text"].replace("<br>", "\n"))
        font = st.sidebar.slider("Tamanho", 10, 24, block["font_size"])
        align = st.sidebar.selectbox(
            "Alinhamento",
            ["left", "center", "right", "justify"],
            index=["left","center","right","justify"].index(block["align"])
        )
        bold = st.sidebar.checkbox("Negrito", block["bold"])
        italic = st.sidebar.checkbox("Itálico", block["italic"])
        if st.sidebar.button("Salvar"):
            st.session_state["blocks"][index] = {
                "type": "text",
                "text": text.replace("\n", "<br>"),
                "font_size": font,
                "align": align,
                "bold": bold,
                "italic": italic,
                "width": width,
                "height": height
            }
            st.session_state["edit_index"] = None
            st.experimental_rerun()

    elif t == "box":
        text = st.sidebar.text_area("Conteúdo", block["text"].replace("<br>", "\n"))
        if st.sidebar.button("Salvar"):
            st.session_state["blocks"][index] = {
                "type": "box",
                "text": text.replace("\n", "<br>"),
                "width": width,
                "height": height
            }
            st.session_state["edit_index"] = None
            st.experimental_rerun()

    elif t == "image":
        caption = st.sidebar.text_input("Legenda", block.get("caption",""))
        if st.sidebar.button("Salvar"):
            block["caption"] = caption
            block["width"] = width
            block["height"] = height
            st.session_state["blocks"][index] = block
            st.session_state["edit_index"] = None
            st.experimental_rerun()

    elif t == "html":
        title = st.sidebar.text_input("Título do enquadramento", block.get("title",""))
        html_code = st.sidebar.text_area("HTML", block["html"], height=250)
        if st.sidebar.button("Salvar"):
            st.session_state["blocks"][index] = {
                "type": "html",
                "title": title,
                "html": html_code,
                "width": width,
                "height": height
            }
            st.session_state["edit_index"] = None
            st.experimental_rerun()


# ============================================================
# STREAMLIT — INTERFACE PRINCIPAL
# ============================================================

def main():
    st.set_page_config(page_title="Editor de Diagnóstico", layout="wide")
    init_state()

    st.title("🧰 Editor de Diagnóstico Interativo (HTML)")

    col_preview, col_side = st.columns([3, 1])

    # -------------------------------------------------------
    # LADO DIREITO — CRIAÇÃO / PROJETO
    # -------------------------------------------------------
    with col_side:
        st.subheader("Novo bloco")

        block_type = st.selectbox(
            "Tipo",
            [
                "Título (capa)",
                "Seção",
                "Texto",
                "Caixa (box)",
                "Divisor (linha)",
                "Imagem",
                "HTML (arquivo externo)"
            ],
        )

        if block_type == "Título (capa)":
            title = st.text_input("Título", "Diagnóstico de Área")
            subtitle = st.text_input("Subtítulo", "Metodologia e Resultados")
            width = st.number_input("Largura (px)", min_value=0, value=0)
            height = st.number_input("Altura (px)", min_value=0, value=0)
            if st.button("Adicionar"):
                st.session_state["blocks"].append({
                    "type": "title",
                    "text": title,
                    "subtitle": subtitle,
                    "width": width,
                    "height": height,
                })

        elif block_type == "Seção":
            text = st.text_input("Nome da seção", "Metodologia")
            width = st.number_input("Largura (px)", min_value=0, value=0)
            height = st.number_input("Altura (px)", min_value=0, value=0)
            if st.button("Adicionar"):
                st.session_state["blocks"].append({
                    "type": "section",
                    "text": text,
                    "width": width,
                    "height": height,
                })

        elif block_type == "Texto":
            text = st.text_area("Texto")
            font_size = st.slider("Tamanho da fonte", 10, 24, 14)
            align = st.selectbox("Alinhamento", ["left", "center", "right", "justify"], index=3)
            bold = st.checkbox("Negrito")
            italic = st.checkbox("Itálico")
            width = st.number_input("Largura (px)", min_value=0, value=0)
            height = st.number_input("Altura (px)", min_value=0, value=0)
            if st.button("Adicionar"):
                st.session_state["blocks"].append({
                    "type": "text",
                    "text": text.replace("\n", "<br>"),
                    "font_size": font_size,
                    "align": align,
                    "bold": bold,
                    "italic": italic,
                    "width": width,
                    "height": height,
                })

        elif block_type == "Caixa (box)":
            text = st.text_area("Conteúdo da caixa")
            width = st.number_input("Largura (px)", min_value=0, value=0)
            height = st.number_input("Altura (px)", min_value=0, value=0)
            if st.button("Adicionar"):
                st.session_state["blocks"].append({
                    "type": "box",
                    "text": text.replace("\n","<br>"),
                    "width": width,
                    "height": height,
                })

        elif block_type == "Divisor (linha)":
            if st.button("Adicionar"):
                st.session_state["blocks"].append({"type": "divider"})

        elif block_type == "Imagem":
            img = st.file_uploader("Imagem", type=["png","jpg","jpeg"])
            caption = st.text_input("Legenda (opcional)")
            width = st.number_input("Largura (px)", min_value=0, value=800)
            height = st.number_input("Altura (px)", min_value=0, value=0)
            if st.button("Adicionar"):
                if img:
                    st.session_state["blocks"].append({
                        "type": "image",
                        "src": image_to_base64(img),
                        "caption": caption,
                        "width": width,
                        "height": height,
                    })
                else:
                    st.warning("Selecione uma imagem primeiro.")

        elif block_type == "HTML (arquivo externo)":
            html_file = st.file_uploader("Arquivo HTML", type=["html","htm"])
            title = st.text_input("Título do enquadramento", "Mapa Interativo")
            width = st.number_input("Largura (px)", min_value=0, value=1000)
            height = st.number_input("Altura (px)", min_value=0, value=600)
            if html_file and st.button("Adicionar"):
                html_code = load_html_file(html_file)
                st.session_state["blocks"].append({
                    "type": "html",
                    "html": html_code,
                    "title": title,
                    "width": width,
                    "height": height,
                })

        # --------- Projeto (salvar / carregar) ----------
        st.markdown("---")
        st.subheader("Projeto")

        if st.button("💾 Salvar projeto"):
            json_bytes = json.dumps(st.session_state["blocks"], ensure_ascii=False).encode("utf-8")
            st.download_button(
                "Baixar .json",
                data=json_bytes,
                file_name="projeto.json",
                mime="application/json"
            )

        projeto_up = st.file_uploader("Carregar projeto (.json)", type=["json"])
        if projeto_up:
            st.session_state["blocks"] = json.loads(projeto_up.read().decode("utf-8"))
            st.success("Projeto carregado!")
            st.experimental_rerun()

    # -------------------------------------------------------
    # LADO ESQUERDO — PRÉVIA + LISTA DE BLOCOS
    # -------------------------------------------------------
    with col_preview:
        st.subheader("Prévia")
        html_preview = build_html(st.session_state["blocks"])
        st.components.v1.html(html_preview, height=720, scrolling=True)

        st.subheader("Blocos")
        for i, block in enumerate(st.session_state["blocks"]):
            cols = st.columns([8, 1, 1, 1, 1])
            with cols[0]:
                st.write(f"{i+1}. {block['type']}")
            with cols[1]:
                if st.button("✏️", key=f"edit_{i}"):
                    st.session_state["edit_index"] = i
            with cols[2]:
                if st.button("⬆️", key=f"up_{i}") and i > 0:
                    st.session_state["blocks"][i-1], st.session_state["blocks"][i] = \
                        st.session_state["blocks"][i], st.session_state["blocks"][i-1]
                    st.experimental_rerun()
            with cols[3]:
                if i < len(st.session_state["blocks"]) - 1 and st.button("⬇️", key=f"down_{i}"):
                    st.session_state["blocks"][i+1], st.session_state["blocks"][i] = \
                        st.session_state["blocks"][i], st.session_state["blocks"][i+1]
                    st.experimental_rerun()
            with cols[4]:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state["blocks"].pop(i)
                    st.experimental_rerun()

        if st.session_state["edit_index"] is not None:
            idx = st.session_state["edit_index"]
            edit_block(idx, st.session_state["blocks"][idx])

        st.markdown("---")
        st.subheader("Exportar HTML")
        final_html = build_html(st.session_state["blocks"])
        st.download_button(
            "📥 Baixar HTML Final",
            data=final_html,
            file_name="diagnostico_interativo.html",
            mime="text/html"
        )


if __name__ == "__main__":
    main()
