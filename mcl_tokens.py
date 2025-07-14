from enum import Enum, auto

# Identificadores y números
IDENTIFICADOR_CODES = {}
NUMERO_CODES = {}
_next_ident_code = 6001
_next_num_code = 7001

# MAPA DE TOKENS
CODIGOS_TOKEN_RESERVADAS = {
    "sustancia": 1010, "numero": 1015, "cadena": 1017, "cantidad": 1020,
    "mostrar": 1090, "mezclar": 1100, "reaccionar": 1110, "balancear": 1120,
    "si": 1130, "sino": 1140, "repetir": 1150, "hacer": 1160,
    "mientras": 1170, "detener": 1180, "y": 1190, "o": 1200,
    "fusionar": 2030,   # mismo código que "+"
    "separar": 2050,    # mismo que "-"
    "catalizar": 2040,  # mismo que "*"
    "diluir": 2060,     # mismo que "/"
    "PLANCK": 1025,     # Nueva constante
    "AVOGADRO": 1026,   # Nueva constante
    "PI": 1027          # Nueva constante
}

OPERADORES_VERBALES = {
    "fusionar": "+",
    "separar": "-",
    "catalizar": "*",
    "diluir": "/"
}

CODIGOS_TOKEN_UNIDADES = {
    "mol": 1030, "gramo": 1040, "atm": 1050, "gradC": 1060, "gradF": 1070, "gradK": 1080,
}

CODIGOS_TOKEN_OPERADORES = {
    "=": 2010, "->": 2020,
    "+": 2030,   # fusionar
    "-": 2050,   # separar
    "*": 2040,   # catalizar
    "/": 2060,   # diluir
    "@": 2070,
    "<": 2080, ">": 2090, "<=": 2100, ">=": 2110, "!=": 2120, "==": 2130,
}

CODIGOS_TOKEN_PUNTUACION = {
    ";": 3010, ",": 3020, ".": 3030, ":": 3050, "#": 3040,
}

CODIGOS_TOKEN_LLAVES = {"{": 4010, "}": 4020}
CODIGOS_TOKEN_PAR_CORCHETE = {"(": 5010, ")": 5020, "[": 5030, "]": 5040}

CODIGOS_TOKEN = {}
for d in (CODIGOS_TOKEN_RESERVADAS, CODIGOS_TOKEN_UNIDADES, CODIGOS_TOKEN_OPERADORES,
          CODIGOS_TOKEN_PUNTUACION, CODIGOS_TOKEN_LLAVES, CODIGOS_TOKEN_PAR_CORCHETE):
    CODIGOS_TOKEN.update(d)

class TipoToken(Enum):
    PALABRA_RESERVADA = auto()
    IDENTIFICADOR = auto()
    NUMERO = auto()
    OPERADOR = auto()
    PUNTUACION = auto()
    LLAVE = auto()
    PAR_CORCHETE = auto()
    UNIDAD = auto()
    TEXTO = auto()
    COMENTARIO = auto()
    DESCONOCIDO = auto()

TOKEN_CATEGORIES = {}
for k in CODIGOS_TOKEN_RESERVADAS: TOKEN_CATEGORIES[k] = TipoToken.PALABRA_RESERVADA
for k in CODIGOS_TOKEN_UNIDADES: TOKEN_CATEGORIES[k] = TipoToken.UNIDAD
for k in CODIGOS_TOKEN_OPERADORES: TOKEN_CATEGORIES[k] = TipoToken.OPERADOR
for k in CODIGOS_TOKEN_PUNTUACION: TOKEN_CATEGORIES[k] = TipoToken.PUNTUACION
for k in CODIGOS_TOKEN_LLAVES: TOKEN_CATEGORIES[k] = TipoToken.LLAVE
for k in CODIGOS_TOKEN_PAR_CORCHETE: TOKEN_CATEGORIES[k] = TipoToken.PAR_CORCHETE

class Token:
    def __init__(self, tipo, valor, inicio, fin):
        global _next_ident_code, _next_num_code
        self.tipo = tipo
        self.valor = valor
        self.inicio = inicio
        self.fin = fin
        if tipo == TipoToken.IDENTIFICADOR:
            if valor not in IDENTIFICADOR_CODES:
                IDENTIFICADOR_CODES[valor] = _next_ident_code
                _next_ident_code += 1
            self.codigo = IDENTIFICADOR_CODES[valor]
        elif tipo == TipoToken.NUMERO:
            if valor not in NUMERO_CODES:
                NUMERO_CODES[valor] = _next_num_code
                _next_num_code += 1
            self.codigo = NUMERO_CODES[valor]
        else:
            self.codigo = CODIGOS_TOKEN.get(valor)

    def to_tuple(self):
        return (self.tipo.name, self.valor, self.codigo or "")