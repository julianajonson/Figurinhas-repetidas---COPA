import os
import re
import sqlite3
import uuid

import pandas as pd
import streamlit as st
from PIL import Image

try:
    from ocr import extrair_codigos
except Exception as erro:
    import streamlit as st
    st.error("Erro ao importar OCR")
    st.write(str(erro))
    extrair_codigos = None


DB_NAME = "figurinhas.db"


def conectar():
    return sqlite3.connect(DB_NAME)


def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS figurinhas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            quantidade INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


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

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT quantidade FROM figurinhas WHERE codigo = ?",
        (codigo,)
    )

    existente = cursor.fetchone()

    if existente:
        nova_quantidade = existente[0] + quantidade

        cursor.execute(
            """
            UPDATE figurinhas
            SET quantidade = ?
            WHERE codigo = ?
            """,
            (nova_quantidade, codigo)
        )
    else:
        cursor.execute(
            """
            INSERT INTO figurinhas (codigo, quantidade)
            VALUES (?, ?)
            """,
            (codigo, quantidade)
        )

    conn.commit()
    conn.close()

    return True


def buscar_figurinha(codigo):
    codigo = normalizar_codigo(codigo)

    if not codigo:
        return None

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT codigo, quantidade
        FROM figurinhas
        WHERE codigo = ?
        """,
        (codigo,)
    )

    resultado = cursor.fetchone()

    conn.close()

    return resultado


def listar_figurinhas():
    conn = conectar()

    df = pd.read_sql_query(
        """
        SELECT codigo, quantidade
        FROM figurinhas
        ORDER BY codigo
        """,
        conn
    )

    conn.close()

    return df


criar_tabela()

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
            use_container_width=True
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
                st.warning(
                    "Inválidas: " + ", ".join(invalidas)
                )


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
            st.success(f"Você possui {resultado[0]}")
            st.write(f"Quantidade: {resultado[1]}")
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