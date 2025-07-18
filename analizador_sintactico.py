from mcl_tokens import *
from simbolos import *

class Parser:
    def __init__(self, tokens, tabla_simbolos):
        self.tokens, self.pos = tokens, 0
        self.tabla_simbolos = tabla_simbolos
        self.errors = []

    @property
    def look(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TipoToken.DESCONOCIDO, "", -1, -1)

    def eat(self, tipo, valor=None):
        if self.look.tipo == tipo and (valor is None or self.look.valor == valor):
            self.pos += 1
        else:
            exp, got = valor or tipo.name, self.look.valor
            self.error(f"Se esperaba: '{exp}', encontrado: '{got}'")

    def error(self, msg):
        self.errors.append(f"[pos {self.pos}] {msg}")
        raise SyntaxError(f"[pos {self.pos}] {msg}")

    def program(self):
        stmts = []
        while self.look.tipo != TipoToken.DESCONOCIDO:
            stmts.append(self.stmt())
        return ("PROGRAM", stmts)

    def stmt(self):
        tp, val = self.look.tipo, self.look.valor
        if tp == TipoToken.PALABRA_RESERVADA:
            if val == "sustancia": return self.cmd_sustancia()
            if val == "numero": return self.cmd_numero()
            if val == "cadena": return self.cmd_cadena()
            if val == "reaccionar": return self.cmd_definir_reaccion()
            if val == "balancear": return self.cmd_balancear()
            if val == "mostrar": return self.cmd_mostrar()
            if val == "mezclar": return self.cmd_mezclar_block()
            if val in ("repetir", "hacer"): return self.cmd_repetir()
            if val == "detener": return self.cmd_detener()
            if val == "si": return self.cmd_si()
        if tp == TipoToken.IDENTIFICADOR:
            if self._peek_val() == "[":
                return self.cmd_llamada()
            return self.cmd_asignacion_or_expr()
        if tp == TipoToken.PUNTUACION and val == ";":
            self.eat(tp, ";")
            return ("EMPTY",)
        if tp == TipoToken.COMENTARIO:
            txt = val
            self.eat(tp)
            return ("COMMENT", txt)
        self.error(f"Sentencia inesperada '{val}'")

    def cmd_sustancia(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "sustancia")
        name = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
        if self.tabla_simbolos.existe_en_actual(name):
            self.error(f"Identificador '{name}' ya declarado")
        self.eat(TipoToken.PALABRA_RESERVADA, "cantidad")
        self.eat(TipoToken.OPERADOR, "=")
        qty = self.look.valor; self.eat(TipoToken.NUMERO)
        try:
            float(qty)
        except ValueError:
            self.error(f"Cantidad '{qty}' no es un número válido")
        unit = None
        if self.look.tipo == TipoToken.UNIDAD:
            unit = self.look.valor; self.eat(TipoToken.UNIDAD)
        meta = []
        if self.look.valor == "@":
            self.eat(TipoToken.OPERADOR, "@")
            self.eat(TipoToken.PAR_CORCHETE, "[")
            while True:
                v = self.look.valor; self.eat(TipoToken.NUMERO)
                try:
                    float(v)
                except ValueError:
                    self.error(f"Metadato '{v}' no es un número válido")
                u = self.look.valor; self.eat(TipoToken.UNIDAD)
                if u not in ["gradC", "atm"]:
                    self.error(f"Unidad '{u}' no válida para metadatos")
                meta.append((v, u))
                if self.look.valor != ",": break
                self.eat(TipoToken.PUNTUACION, ",")
            self.eat(TipoToken.PAR_CORCHETE, "]")
        self.eat(TipoToken.PUNTUACION, ";")
        simbolo = Simbolo(name, "sustancia", cantidad=qty, unidad=unit, metadatos=meta)
        self.tabla_simbolos.insertar(name, simbolo)
        return ("SUSTANCIA", name, qty, unit, meta)

    def cmd_numero(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "numero")
        name = self.look.valor
        self.eat(TipoToken.IDENTIFICADOR)
        if self.tabla_simbolos.existe_en_actual(name):
            self.error(f"Identificador '{name}' ya declarado")
        self.eat(TipoToken.OPERADOR, "=")
        value_expr = self.expr()
        expr_type, _ = self._infer_type(value_expr)
        if expr_type != "numero":
            self.error(f"La expresión debe ser de tipo número, no {expr_type}")
        self.eat(TipoToken.PUNTUACION, ";")
        simbolo = Simbolo(name, "numero", valor=value_expr)
        self.tabla_simbolos.insertar(name, simbolo)
        return ("NUMERO", name, value_expr)

    def cmd_cadena(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "cadena")
        name = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
        if self.tabla_simbolos.existe_en_actual(name):
            self.error(f"Identificador '{name}' ya declarado")
        self.eat(TipoToken.OPERADOR, "=")
        value = self.look.valor; self.eat(TipoToken.TEXTO)
        self.eat(TipoToken.PUNTUACION, ";")
        simbolo = Simbolo(name, "cadena", valor=value)
        self.tabla_simbolos.insertar(name, simbolo)
        return ("CADENA", name, value)

    def cmd_asignacion_or_expr(self):
        name = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
        if self.look.valor in (".", "=>"):
            op = self.look.valor
            self.eat(TipoToken.PUNTUACION if op == "." else TipoToken.OPERADOR, op)
            prop = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
            if self.look.valor == "=":
                self.eat(TipoToken.OPERADOR, "=")
                expr = self.expr()
                expr_type, expr_unit = self._infer_type(expr)
                simbolo = self.tabla_simbolos.buscar(name)
                if simbolo is None:
                    self.error(f"Variable '{name}' no declarada para asignación")
                if simbolo.tipo != "sustancia":
                    self.error(f"'{name}' debe ser una sustancia para asignar a la propiedad '{prop}'")
                if prop == "cant":
                    if expr_type != "numero":
                        self.error(f"Asignación a 'cant' debe ser de tipo número, no {expr_type}")
                    if simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
                        self.error(f"Incompatibilidad de unidades: '{name}' tiene '{simbolo.info['unidad']}', expresión tiene '{expr_unit}'")
                elif prop in ["temp", "presion"]:
                    if expr_type != "numero":
                        self.error(f"Asignación a '{prop}' debe ser de tipo número, no {expr_type}")
                    expected_unit = "gradC" if prop == "temp" else "atm"
                    if expr_unit != expected_unit:
                        self.error(f"Incompatibilidad de unidades: '{prop}' requiere '{expected_unit}', expresión tiene '{expr_unit}'")
                else:
                    self.error(f"Propiedad desconocida '{prop}' para la sustancia '{name}'")
                self.eat(TipoToken.PUNTUACION, ";")
                return ("ASIGNACION", ("PROP_ACCESS", name, prop), expr)
        if self.look.valor == "=":
            self.eat(TipoToken.OPERADOR, "=")
            expr = self.expr()
            expr_type, expr_unit = self._infer_type(expr)
            simbolo = self.tabla_simbolos.buscar(name)
            if simbolo is None:
                self.error(f"Variable '{name}' no declarada para asignación")
            if expr_type != simbolo.tipo:
                self.error(f"Asignación incompatible: '{name}' es de tipo {simbolo.tipo}, pero la expresión es de tipo {expr_type}")
            if simbolo.tipo == "sustancia" and simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
                self.error(f"Incompatibilidad de unidades: '{name}' tiene '{simbolo.info['unidad']}', expresión tiene '{expr_unit}'")
            self.eat(TipoToken.PUNTUACION, ";")
            return ("ASIGNACION", name, expr)
        expr = ("VAR", name)
        return ("EXPRESSION", expr)

    def cmd_definir_reaccion(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "reaccionar")
        name = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
        if self.tabla_simbolos.existe_en_actual(name):
            self.error(f"Reacción '{name}' ya declarada")
        self.eat(TipoToken.PAR_CORCHETE, "[")
        react = self._lista_reactivos()
        self.eat(TipoToken.OPERADOR, "->")
        prod = self._lista_reactivos()
        self.eat(TipoToken.PAR_CORCHETE, "]")
        self._validar_reaccion(react, prod, name)
        simbolo_reaccion = Simbolo(name, "reaccion", reactivos=react, productos=prod)
        self.tabla_simbolos.insertar(name, simbolo_reaccion)
        self.tabla_simbolos.entrar_bloque()
        for _, param in react + prod:
            if self.tabla_simbolos.existe_en_actual(param):
                self.error(f"Parámetro '{param}' duplicado")
            self.tabla_simbolos.insertar(param, Simbolo(param, "sustancia"))
        body = self.bloque()
        self.tabla_simbolos.salir_bloque()
        return ("DEF_REACCION", name, react, prod, body)

    def cmd_llamada(self):
        name = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
        simbolo = self.tabla_simbolos.buscar(name)
        if simbolo is None or simbolo.tipo != "reaccion":
            self.error(f"Reacción '{name}' no declarada")
        self.eat(TipoToken.PAR_CORCHETE, "[")
        args = self._lista_reactivos()
        self.eat(TipoToken.PAR_CORCHETE, "]")
        self.eat(TipoToken.PUNTUACION, ";")
        expected = [(coeff, name) for coeff, name in simbolo.info["reactivos"]]
        if len(args) != len(expected):
            self.error(f"La reacción '{name}' espera {len(expected)} reactivos, pero se dieron {len(args)}")
        for (c1, n1), (c2, n2) in zip(expected, args):
            if n1 != n2 or c1 != c2:
                self.error(f"Reactivo esperado: {c1}{n1}, encontrado: {c2}{n2}")
        return ("CALL", name, args)

    def cmd_mezclar_block(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "mezclar")
        self.eat(TipoToken.PAR_CORCHETE, "(")
        expr = self.expr()
        self.eat(TipoToken.PAR_CORCHETE, ")")
        self.eat(TipoToken.OPERADOR, "->")
        tgt = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
        simbolo = self.tabla_simbolos.buscar(tgt)
        if simbolo is None:
            # Implicitly declare the target substance and include it in the AST
            simbolo = Simbolo(tgt, "sustancia", cantidad="0", unidad=None, metadatos=[])
            self.tabla_simbolos.insertar(tgt, simbolo)
        elif simbolo.tipo != "sustancia":
            self.error(f"Destino '{tgt}' no es una sustancia declarada")
        expr_type, expr_unit = self._infer_type(expr)
        if expr_type != "sustancia":
            self.error(f"La expresión en 'mezclar' debe ser de tipo sustancia, no {expr_type}")
        if simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
            self.error(f"Incompatibilidad de unidades: destino tiene '{simbolo.info['unidad']}', expresión tiene '{expr_unit}'")
        self.eat(TipoToken.PUNTUACION, ";")
        return ("MEZCLAR", expr, ("SUSTANCIA", tgt, "0", None, []))  # Include implicit declaration in AST

    def cmd_balancear(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "balancear")
        e = self.expr()
        self.eat(TipoToken.PUNTUACION, ";")
        expr_type, _ = self._infer_type(e)
        if expr_type != "sustancia":
            self.error(f"La expresión en 'balancear' debe ser de tipo sustancia, no {expr_type}")
        return ("BALANCEAR", e)

    def cmd_mostrar(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "mostrar")
        self.eat(TipoToken.PAR_CORCHETE, "(")
        args = []
        while True:
            if self.look.tipo == TipoToken.TEXTO:
                v = self.look.valor; self.eat(TipoToken.TEXTO)
                args.append(("TEXT", v))
            else:
                v = self.expr()
                expr_type, _ = self._infer_type(v)
                if expr_type not in ["sustancia", "numero", "cadena"]:
                    self.error(f"Argumentos de 'mostrar' deben ser sustancia, número, cadena o texto, no {expr_type}")
                args.append(v)
            if self.look.valor != ",": break
            self.eat(TipoToken.PUNTUACION, ",")
        self.eat(TipoToken.PAR_CORCHETE, ")")
        self.eat(TipoToken.PUNTUACION, ";")
        return ("MOSTRAR", args)

    def cmd_si(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "si")
        self.eat(TipoToken.PAR_CORCHETE, "(")
        c = self.cond()
        self.eat(TipoToken.PAR_CORCHETE, ")")
        b1 = self.bloque()
        b2 = None
        if self.look.valor == "sino":
            self.eat(TipoToken.PALABRA_RESERVADA, "sino")
            b2 = self.bloque()
        return ("SI", c, b1, b2)

    def cmd_repetir(self):
        if self.look.valor == "repetir":
            self.eat(TipoToken.PALABRA_RESERVADA, "repetir")
            b = self.bloque()
            self.eat(TipoToken.PALABRA_RESERVADA, "mientras")
            self.eat(TipoToken.PAR_CORCHETE, "(")
            c = self.cond()
            self.eat(TipoToken.PAR_CORCHETE, ")")
            self.eat(TipoToken.PUNTUACION, ";")
            return ("REPETIR_HASTA", c, b)
        self.eat(TipoToken.PALABRA_RESERVADA, "hacer")
        b = self.bloque()
        self.eat(TipoToken.PALABRA_RESERVADA, "mientras")
        self.eat(TipoToken.PAR_CORCHETE, "(")
        c = self.cond()
        self.eat(TipoToken.PAR_CORCHETE, ")")
        self.eat(TipoToken.PUNTUACION, ";")
        return ("HACER_MIENTRAS", c, b)

    def cmd_detener(self):
        self.eat(TipoToken.PALABRA_RESERVADA, "detener")
        self.eat(TipoToken.PUNTUACION, ";")
        return ("DETENER",)

    def bloque(self):
        self.eat(TipoToken.LLAVE, "{")
        self.tabla_simbolos.entrar_bloque()
        stmts = []
        while not (self.look.tipo == TipoToken.LLAVE and self.look.valor == "}"):
            stmts.append(self.stmt())
        self.eat(TipoToken.LLAVE, "}")
        self.tabla_simbolos.salir_bloque()
        return ("BLOQUE", stmts)

    def expr(self):
        node = self.term()
        while self.look.tipo == TipoToken.OPERADOR and self.look.valor in ("+", "-"):
            op = self.look.valor
            self.eat(TipoToken.OPERADOR, op)
            right = self.term()
            left_type, left_unit = self._infer_type(node)
            right_type, right_unit = self._infer_type(right)
            if op in ["+", "-"]:
                if left_type == right_type == "sustancia":
                    if left_unit != right_unit:
                        self.error(f"Incompatibilidad de unidades: {left_unit} y {right_unit}")
                    node = ("BIN_OP", op, node, right)
                elif left_type == "cadena" and right_type == "cadena" and op == "+":
                    node = ("BIN_OP", op, node, right)
                elif left_type == right_type == "numero":
                    node = ("BIN_OP", op, node, right)
                else:
                    self.error(f"Operador '{op}' no válido entre tipos {left_type} y {right_type}")
        return node

    def term(self):
        if self.look.tipo == TipoToken.PALABRA_RESERVADA and self.look.valor in OPERADORES_VERBALES:
            v = OPERADORES_VERBALES[self.look.valor]
            self.eat(TipoToken.PALABRA_RESERVADA)
            return ("VAR", v)
        
        node = self.factor()
        while self.look.tipo == TipoToken.OPERADOR and self.look.valor in ("*", "/"):
            op = self.look.valor
            self.eat(TipoToken.OPERADOR, op)
            right = self.factor()
            left_type, left_unit = self._infer_type(node)
            right_type, right_unit = self._infer_type(right)
            if (left_type == "sustancia" and right_type == "numero") or \
            (left_type == "numero" and right_type == "numero"):
                node = ("BIN_OP", op, node, right)
            else:
                self.error(f"Operador '{op}' no válido entre tipos {left_type} y {right_type}")
        return node

    def factor(self):
        if self.look.tipo == TipoToken.IDENTIFICADOR or self.look.tipo == TipoToken.PALABRA_RESERVADA:
            v = self.look.valor
            if self.look.tipo == TipoToken.PALABRA_RESERVADA and v in ["PLANCK", "AVOGADRO", "PI"]:
                self.eat(TipoToken.PALABRA_RESERVADA)
            else:
                self.eat(TipoToken.IDENTIFICADOR)
            simbolo = self.tabla_simbolos.buscar(v)
            if simbolo is None:
                self.error(f"Variable '{v}' no declarada")
            # Check for property access
            if self.look.valor in (".", "=>"):
                op = self.look.valor
                self.eat(TipoToken.PUNTUACION if op == "." else TipoToken.OPERADOR, op)
                prop = self.look.valor
                self.eat(TipoToken.IDENTIFICADOR)
                return ("PROP_ACCESS", v, prop)
            return ("VAR", v)
        if self.look.tipo == TipoToken.NUMERO:
            v = self.look.valor; self.eat(TipoToken.NUMERO)
            return ("NUM", v)
        if self.look.tipo == TipoToken.TEXTO:
            v = self.look.valor; self.eat(TipoToken.TEXTO)
            return ("TEXT", v)
        if self.look.valor == "(":
            self.eat(TipoToken.PAR_CORCHETE, "(")
            node = self.expr()
            self.eat(TipoToken.PAR_CORCHETE, ")")
            return node
        self.error(f"Factor inesperado '{self.look.valor}'")

    def cond(self):
        left = self.expr()
        op = self.look.valor
        if op not in ["==", "!=", "<", ">", "<=", ">="]:
            self.error(f"Operador de comparación '{op}' no válido")
        self.eat(TipoToken.OPERADOR, op)
        right = self.expr()
        left_type, left_unit = self._infer_type(left)
        right_type, right_unit = self._infer_type(right)
        if left_type != right_type:
            self.error(f"Comparación entre tipos incompatibles: {left_type} y {right_type}")
        if left_type == "sustancia" and left_unit != right_unit:
            self.error(f"Incompatibilidad de unidades en comparación: {left_unit} y {right_unit}")
        node = ("COND", op, left, right)
        while self.look.valor in ("y", "o"):
            conj = self.look.valor; self.eat(TipoToken.PALABRA_RESERVADA, conj)
            nxt = self.cond()
            node = ("LOGIC", conj, node, nxt)
        return node

    def _lista_reactivos(self):
        items = []
        while True:
            coeff = "1"
            if self.look.tipo == TipoToken.NUMERO:
                coeff = self.look.valor; self.eat(TipoToken.NUMERO)
            name = self.look.valor; self.eat(TipoToken.IDENTIFICADOR)
            simbolo = self.tabla_simbolos.buscar(name)
            if simbolo is None or simbolo.tipo != "sustancia":
                self.error(f"Reactivo '{name}' no es una sustancia declarada")
            items.append((coeff, name))
            if self.look.valor != ",": break
            self.eat(TipoToken.PUNTUACION, ",")
        return items

    def _infer_type(self, node):
        if isinstance(node, tuple):
            if node[0] == "VAR":
                simbolo = self.tabla_simbolos.buscar(node[1])
                if not simbolo:
                    self.error(f"Variable '{node[1]}' no declarada")
                return simbolo.tipo, simbolo.info.get("unidad")
            if node[0] == "PROP_ACCESS":
                var, prop = node[1], node[2]
                simbolo = self.tabla_simbolos.buscar(var)
                if not simbolo:
                    self.error(f"Variable '{var}' no declarada")
                if simbolo.tipo != "sustancia":
                    self.error(f"'{var}' debe ser una sustancia para acceder a la propiedad '{prop}'")
                if prop == "cant":
                    return "numero", simbolo.info.get("unidad")
                elif prop in ["temp", "presion"]:
                    # Check if the property exists in metadatos
                    for v, u in simbolo.info.get("metadatos", []):
                        if (prop == "temp" and u == "gradC") or (prop == "presion" and u == "atm"):
                            return "numero", u
                    self.error(f"Propiedad '{prop}' no definida para la sustancia '{var}'")
                else:
                    self.error(f"Propiedad desconocida '{prop}' para la sustancia '{var}'")
                return "desconocido", None
            if node[0] == "NUM":
                return "numero", None
            if node[0] == "TEXT":
                return "cadena", None
            if node[0] == "BIN_OP":
                op, left, right = node[1], node[2], node[3]
                left_type, left_unit = self._infer_type(left)
                right_type, right_unit = self._infer_type(right)
                if op in ["+", "-"] and left_type == right_type == "sustancia":
                    if left_unit != right_unit:
                        self.error(f"Incompatibilidad de unidades: {left_unit} y {right_unit}")
                    return "sustancia", left_unit
                if op == "+" and left_type == right_type == "cadena":
                    return "cadena", None
                if op in ["+", "-"] and left_type == right_type == "numero":
                    return "numero", None
                if op in ["*", "/"] and left_type == "sustancia" and right_type == "numero":
                    return "sustancia", left_unit
                if op in ["*", "/"] and left_type == right_type == "numero":
                    return "numero", None
                self.error(f"Operación '{op}' no válida entre {left_type} y {right_type}")
        return "desconocido", None

    def _validar_reaccion(self, reactivos, productos, nombre_reaccion):
        for _, name in reactivos + productos:
            simbolo = self.tabla_simbolos.buscar(name)
            if simbolo is None or simbolo.tipo != "sustancia":
                self.error(f"En reacción '{nombre_reaccion}', '{name}' no es una sustancia declarada")
        if not reactivos or not productos:
            self.error(f"La reacción '{nombre_reaccion}' debe tener al menos un reactivo y un producto")

    def _peek_val(self):
        return self.tokens[self.pos + 1].valor if self.pos + 1 < len(self.tokens) else None