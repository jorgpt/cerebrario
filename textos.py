import re
import unicodedata

RE_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
RE_INVISIBLES = re.compile(r"[\u00ad\u061c\u180e\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u206f\ufeff\ufff9-\ufffb]")
RE_CORTES = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
ETIQUETAS = str.maketrans({"<": "‹", ">": "›"})


def sin_control(texto):
    return RE_CONTROL.sub("?", str(texto))


def sin_marcas(texto):
    minusculas = texto.lower()
    if minusculas.isascii():
        return minusculas
    return "".join(c for c in unicodedata.normalize("NFKD", minusculas) if not unicodedata.category(c).startswith("M"))


def decimal(valor, digitos=1):
    return format(valor, f".{digitos}f").replace(".", ",")


def miles(n):
    return format(n, ",").replace(",", ".")


def cantidad(n, singular, plural):
    return f"{miles(n)} {singular if n == 1 else plural}"


def detalle(error):
    texto = f"{type(error).__name__}: {error}" if str(error) else type(error).__name__
    return f"detalle de Python, en inglés: {sin_control(texto)}"


def limpiar(texto):
    return RE_CORTES.sub(" ", RE_INVISIBLES.sub("", str(texto))).translate(ETIQUETAS)


def citar(texto, largo=None):
    limpio = " ".join(limpiar(texto).split()).replace("«", "‹").replace("»", "›")
    if largo and len(limpio) > largo:
        limpio = limpio[:largo - 1].rstrip() + "…"
    return "«" + limpio + "»"
