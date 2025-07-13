import re
from mcl_tokens import *

class TrieNode:
    def __init__(self):
        self.hijos = {}
        self.fin = False
        self.token = None

class Trie:
    def __init__(self):
        self.raiz = TrieNode()
        for palabra in list(CODIGOS_TOKEN_RESERVADAS) + list(CODIGOS_TOKEN_UNIDADES):
            nodo = self.raiz
            for c in palabra:
                nodo = nodo.hijos.setdefault(c, TrieNode())
            nodo.fin, nodo.token = True, palabra

    def buscar(self, texto, inicio):
        nodo, i = self.raiz, inicio
        match_token, match_end = None, inicio
        while i < len(texto) and (texto[i].isalnum() or texto[i] == '_'):
            c = texto[i]
            if c not in nodo.hijos:
                break
            nodo, i = nodo.hijos[c], i + 1
            if nodo.fin:
                match_token, match_end = nodo.token, i
        return match_token, match_end

class AFD_Lexico:
    def __init__(self, texto):
        self.texto, self.i = texto, 0
        self.n = len(texto)
        self.tokens = []
        self.trie = Trie()
        self.delims = set(' \t\n"={}[]();,.:#')

    def emitir(self, tipo, valor, inicio, fin):
        self.tokens.append(Token(tipo, valor, inicio, fin))

    def run(self):
        while self.i < self.n:
            c = self.texto[self.i]
            if c.isspace():
                self.i += 1
                continue
            inicio = self.i
            if c.isalpha():
                j, err = self.i, False
                while j < self.n and self.texto[j] not in self.delims:
                    if not (self.texto[j].isalnum() or self.texto[j] == '_'):
                        err = True
                    j += 1
                lex = self.texto[inicio:j]
                palabra, fin = (None, None)
                if not err:
                    palabra, fin = self.trie.buscar(lex, 0)
                    if palabra and fin != len(lex):
                        palabra = None
                if palabra:
                    # CONVERTIR PALABRAS A OPERADORES
                    if palabra in OPERADORES_VERBALES:
                        tipo_token = TipoToken.OPERADOR
                        valor_token = OPERADORES_VERBALES[palabra]
                        self.emitir(tipo_token, valor_token, inicio, j)
                    else:
                        tipo = TOKEN_CATEGORIES[lex]
                        self.emitir(tipo, lex, inicio, j)
                else:
                    tp = TipoToken.IDENTIFICADOR if not err else TipoToken.DESCONOCIDO
                    self.emitir(tp, lex, inicio, j)
                self.i = j
                continue
            if c.isdigit():
                while self.i < self.n and self.texto[self.i].isdigit():
                    self.i += 1
                if self.i < self.n and self.texto[self.i] == '.':
                    self.i += 1
                    while self.i < self.n and self.texto[self.i].isdigit():
                        self.i += 1
                val = self.texto[inicio:self.i]
                self.emitir(TipoToken.NUMERO, val, inicio, self.i)
                continue
            if c == '"':
                self.i += 1
                closed = False
                while self.i < self.n:
                    if self.texto[self.i] == '"':
                        closed = True
                        self.i += 1
                        break
                    self.i += 1
                lex = self.texto[inicio:self.i]
                tp = TipoToken.TEXTO if closed else TipoToken.DESCONOCIDO
                self.emitir(tp, lex, inicio, self.i)
                continue
            if c == '#':
                while self.i < self.n and self.texto[self.i] != '\n':
                    self.i += 1
                lex = self.texto[inicio:self.i]
                self.emitir(TipoToken.COMENTARIO, lex, inicio, self.i)
                continue
            two = self.texto[self.i:self.i+2]
            if two in CODIGOS_TOKEN_OPERADORES:
                self.i += 2
                self.emitir(TipoToken.OPERADOR, two, inicio, self.i)
                continue
            if c in CODIGOS_TOKEN_OPERADORES:
                self.i += 1
                self.emitir(TipoToken.OPERADOR, c, inicio, self.i)
                continue
            if c in CODIGOS_TOKEN_LLAVES:
                self.i += 1
                self.emitir(TipoToken.LLAVE, c, inicio, self.i)
                continue
            if c in CODIGOS_TOKEN_PAR_CORCHETE:
                self.i += 1
                self.emitir(TipoToken.PAR_CORCHETE, c, inicio, self.i)
                continue
            if c in CODIGOS_TOKEN_PUNTUACION:
                self.i += 1
                self.emitir(TipoToken.PUNTUACION, c, inicio, self.i)
                continue
            self.i += 1
            self.emitir(TipoToken.DESCONOCIDO, c, inicio, self.i)
        return self.tokens