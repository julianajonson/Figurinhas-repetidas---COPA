import os
import re
import uuid

import pandas as pd
import streamlit as st
from PIL import Image
from supabase import create_client

try:
    from ocr import extrair_codigos
except Exception as erro:
    st.error("Erro ao importar OCR")
    st.write(str(erro))
    extrair_codigos = None


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalizar_codigo(codigo):
    codigo = codigo.upper().strip()
    codigo = re.sub(r"\s+", " ", codigo)

    match = re.search(r"\b([A-Z]{3})\s?(\d{1,2})\b", codigo)

    if match:
        return f"{match.group(1)} {match.group(2)}"

    return None


def cadastrar_figurinha(codigo, quantidade=1):
    codigo = normalizar_codigo(codigo)

    if not codigo:
        return False

    existente = (
        supabase.table("figurinhas")
        .select("*")
        .eq("codigo", codigo)
        .execute()
    )

    if existente.data:
        atual = existente.data[0]
        nova_quantidade = atual["quantidade"] + quantidade

        supabase.table("figurinhas").update(
            {"quantidade": nova_quantidade}
        ).eq("codigo", codigo).execute()

    else:
        supabase.table("figurinhas").insert(
            {
                "codigo": codigo,
                "quantidade": quantidade,
            }
        ).execute()

    return True


def buscar_figurinha(codigo):
    codigo = normalizar_codigo(codigo)

    if not codigo:
        return None

    resultado = (
        supabase.table("figurinhas")
        .select("*")
        .eq("codigo", codigo)
        .execute()
    )

    if resultado.data:
        return resultado.data[0]

    return None

def excluir_figurinha(codigo):
    codigo = normalizar_codigo(codigo)

    if not codigo:
        return False

    resultado = buscar_figurinha(codigo)

    if not resultado:
        return False

    supabase.table("figurinhas").delete().eq("codigo", codigo).execute()

    return True

def listar_figurinhas():
    resultado = (
        supabase.table("figurinhas")
        .select("codigo, quantidade")
        .order("codigo")
        .execute()
    )

    return pd.DataFrame(resultado.data)


st.set_page_config(
    page_title="Figurinhas da Copa",
    page_icon="⚽"
)

st.title("⚽ Controle de Figurinhas Repetidas")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Cadastrar por foto",
        "Cadastrar manualmente",
        "Buscar figurinha",
        "Listar repetidas",
        "Excluir figurinha"
    ],
)


if menu == "Cadastrar por foto":

    st.header("Cadastrar figurinhas por foto")

    foto = st.file_uploader(
        "Envie uma foto",
        type=["jpg", "jpeg", "png"]
    )

    if foto:

        os.makedirs("uploads", exist_ok=True)

        extensao = foto.name.split(".")[-1]
        nome_arquivo = f"{uuid.uuid4()}.{extensao}"
        caminho = os.path.join("uploads", nome_arquivo)

        with open(caminho, "wb") as arquivo:
            arquivo.write(foto.getbuffer())

        imagem = Image.open(foto)

        st.image(
            imagem,
            caption="Foto enviada",
            width="stretch"
        )

        if extrair_codigos:

            if st.button("🔍 Detectar códigos automaticamente"):

                try:
                    codigos_detectados = extrair_codigos(caminho)

                    if codigos_detectados:
                        st.success(
                            f"{len(codigos_detectados)} códigos detectados"
                        )

                        st.session_state["codigos_detectados"] = "\n".join(
                            codigos_detectados
                        )

                    else:
                        st.warning("Nenhum código detectado.")
                        st.session_state["codigos_detectados"] = ""

                except Exception as erro:
                    st.error(
                        "Não foi possível usar o OCR automático neste ambiente."
                    )
                    st.info("Digite os códigos manualmente abaixo.")
                    st.write(str(erro))
                    st.session_state["codigos_detectados"] = ""

        else:
            st.warning("OCR não está disponível neste ambiente.")

        codigos_texto = st.text_area(
            "Confirme ou edite os códigos",
            value=st.session_state.get("codigos_detectados", ""),
            height=180,
            placeholder="SWE 2\nBIH 10\nBIH 8\nTUN 13"
        )

        if st.button("Cadastrar figurinhas da foto"):

            codigos = [
                c.strip()
                for c in codigos_texto.splitlines()
                if c.strip()
            ]

            cadastradas = 0
            invalidas = []

            for codigo in codigos:
                sucesso = cadastrar_figurinha(codigo, 1)

                if sucesso:
                    cadastradas += 1
                else:
                    invalidas.append(codigo)

            st.success(f"{cadastradas} figurinhas cadastradas.")

            if invalidas:
                st.warning("Inválidas: " + ", ".join(invalidas))


elif menu == "Cadastrar manualmente":

    st.header("Cadastrar manualmente")

    codigo = st.text_input(
        "Código",
        placeholder="TUN 13"
    )

    quantidade = st.number_input(
        "Quantidade",
        min_value=1,
        value=1
    )

    if st.button("Cadastrar"):

        sucesso = cadastrar_figurinha(
            codigo,
            int(quantidade)
        )

        if sucesso:
            st.success("Figurinha cadastrada.")
        else:
            st.error("Código inválido.")


elif menu == "Buscar figurinha":

    st.header("Buscar figurinha")

    codigo = st.text_input(
        "Digite o código",
        placeholder="TUN 13"
    )

    if st.button("Buscar"):

        resultado = buscar_figurinha(codigo)

        if resultado:
            st.success(f"Você possui {resultado['codigo']}")
            st.write(f"Quantidade: {resultado['quantidade']}")
        else:
            st.error("Figurinha não encontrada.")


elif menu == "Listar repetidas":

    st.header("Figurinhas repetidas")

    df = listar_figurinhas()

    if df.empty:
        st.info("Nenhuma figurinha cadastrada.")
    else:
        st.dataframe(
            df,
            use_container_width=True
        )
    
elif menu == "Excluir figurinha":

    st.header("Excluir figurinha")

    codigo = st.text_input(
        "Digite o código da figurinha que deseja excluir",
        placeholder="Ex: TUN 13"
    )

    if st.button("Buscar para excluir"):

        resultado = buscar_figurinha(codigo)

        if resultado:
            st.session_state["codigo_para_excluir"] = resultado["codigo"]
            st.success(
                f"Figurinha encontrada: {resultado['codigo']} | Quantidade: {resultado['quantidade']}"
            )
        else:
            st.error("Figurinha não encontrada.")

    if "codigo_para_excluir" in st.session_state:

        st.warning(
            f"Tem certeza que deseja excluir {st.session_state['codigo_para_excluir']}?"
        )

        if st.button("Confirmar exclusão"):

            sucesso = excluir_figurinha(
                st.session_state["codigo_para_excluir"]
            )

            if sucesso:
                st.success("Figurinha excluída com sucesso.")
                del st.session_state["codigo_para_excluir"]
            else:
                st.error("Erro ao excluir figurinha.")