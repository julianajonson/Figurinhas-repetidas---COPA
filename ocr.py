import re
import cv2
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()


def normalizar_codigo(codigo):
    codigo = codigo.upper().strip()
    codigo = re.sub(r"\s+", " ", codigo)

    match = re.search(r"\b([A-Z]{3})\s?(\d{1,2})\b", codigo)

    if match:
        return f"{match.group(1)} {match.group(2)}"

    return None


def extrair_codigos(imagem_path):
    try:
        img = cv2.imread(imagem_path)

        if img is None:
            return []

        result, _ = ocr(img)

        codigos = []

        if result:
            for item in result:
                texto = item[1].upper()

                encontrados = re.findall(r"\b[A-Z]{3}\s?\d{1,2}\b", texto)

                for encontrado in encontrados:
                    codigo = normalizar_codigo(encontrado)

                    if codigo:
                        codigos.append(codigo)

        return sorted(list(set(codigos)))

    except Exception as erro:
        print("Erro OCR:", erro)
        return []