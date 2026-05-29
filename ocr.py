import re
import cv2
import easyocr


def normalizar_codigo(codigo):
    codigo = codigo.upper().strip()
    codigo = re.sub(r"\s+", " ", codigo)

    match = re.search(r"\b([A-Z]{3})\s?(\d{1,2})\b", codigo)

    if match:
        return f"{match.group(1)} {match.group(2)}"

    return None


def extrair_codigos(imagem_path):
    try:
        reader = easyocr.Reader(["en"], gpu=False)

        imagem = cv2.imread(imagem_path)

        if imagem is None:
            return []

        resultados = reader.readtext(imagem)

        codigos = []

        for resultado in resultados:
            texto = resultado[1].upper()

            encontrados = re.findall(r"\b[A-Z]{3}\s?\d{1,2}\b", texto)

            for item in encontrados:
                codigo = normalizar_codigo(item)

                if codigo:
                    codigos.append(codigo)

        return sorted(list(set(codigos)))

    except Exception as erro:
        print("Erro no OCR:", erro)
        return []