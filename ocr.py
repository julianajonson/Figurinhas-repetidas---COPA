import re
import cv2
import easyocr

reader = easyocr.Reader(['en'])


def normalizar_codigo(codigo):
    codigo = codigo.upper().strip()
    codigo = re.sub(r'\s+', ' ', codigo)

    match = re.search(r'\b([A-Z]{3})\s?(\d{1,2})\b', codigo)

    if match:
        letras = match.group(1)
        numero = match.group(2)
        return f"{letras} {numero}"

    return None


def extrair_codigos(imagem_path):
    try:
        imagem = cv2.imread(imagem_path)

        if imagem is None:
            return []

        resultados = reader.readtext(imagem)

        textos = [resultado[1] for resultado in resultados]

        codigos = []

        for texto in textos:
            texto = texto.upper()

            encontrados = re.findall(r'\b[A-Z]{3}\s?\d{1,2}\b', texto)

            for item in encontrados:
                codigo = normalizar_codigo(item)

                if codigo:
                    codigos.append(codigo)

        return sorted(list(set(codigos)))

    except Exception as erro:
        print("Erro OCR:", erro)
        return []