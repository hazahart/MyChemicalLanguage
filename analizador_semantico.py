from mcl_tokens import *
from simbolos import *

class AnalizadorSemantico:
    def __init__(self, ast, tabla_simbolos):
        self.ast = ast
        self.tabla_simbolos = tabla_simbolos
        self.errores = []

    def analizar(self):
        self._recorrer_ast(self.ast)
        return self.errores

    def _recorrer_ast(self, nodo):
        if isinstance(nodo, tuple):
            tipo = nodo[0]
            if tipo == "SUSTANCIA":
                self._verificar_sustancia(nodo)
            elif tipo == "NUMERO":
                self._verificar_numero(nodo)
            elif tipo == "CADENA":
                self._verificar_cadena(nodo)
            elif tipo == "ASIGNACION":
                self._verificar_asignacion(nodo)
            elif tipo == "DEF_REACCION":
                self._verificar_reaccion(nodo)
            elif tipo == "CALL":
                self._verificar_llamada(nodo)
            elif tipo == "MEZCLAR":
                self._verificar_mezclar(nodo)
            elif tipo == "BALANCEAR":
                self._verificar_balancear(nodo)
            elif tipo == "MOSTRAR":
                self._verificar_mostrar(nodo)
            elif tipo in ("SI", "REPETIR_HASTA", "HACER_MIENTRAS"):
                self._verificar_control(nodo)

            # Recorrer hijos
            for elemento in nodo[1:]:
                self._recorrer_ast(elemento)

    def _verificar_sustancia(self, nodo):
        _, name, qty, unit, meta = nodo
        try:
            float(qty)
        except ValueError:
            self.errores.append(f"Cantidad '{qty}' no es un número válido")

        if unit and unit not in CODIGOS_TOKEN_UNIDADES:
            self.errores.append(f"Unidad '{unit}' no reconocida")

        for v, u in meta:
            try:
                float(v)
            except ValueError:
                self.errores.append(f"Metadato '{v}' no es un número válido")
            if u not in ["gradC", "atm"]:
                self.errores.append(f"Unidad de metadato '{u}' no válida")

    def _verificar_numero(self, nodo):
        _, name, expr = nodo
        simbolo = self.tabla_simbolos.buscar(name)
        if not simbolo:
            self.errores.append(f"Variable '{name}' no declarada")
            return

        expr_type, _ = self._infer_type(expr)
        if expr_type != "numero":
            self.errores.append(f"Expresión para número '{name}' debe ser numérica")

    def _verificar_cadena(self, nodo):
        _, name, value = nodo
        if not isinstance(value, str) or not (value.startswith('"') and value.endswith('"')):
            self.errores.append(f"Valor de cadena '{name}' no es válido")

    def _verificar_asignacion(self, nodo):
        _, target, expr = nodo
        if isinstance(target, tuple) and target[0] == "PROP_ACCESS":
            var, prop = target[1], target[2]
            simbolo = self.tabla_simbolos.buscar(var)
            if not simbolo:
                self.errores.append(f"Variable '{var}' no declarada")
                return
            if simbolo.tipo != "sustancia":
                self.errores.append(f"'{var}' debe ser una sustancia para asignar a la propiedad '{prop}'")
                return
            expr_type, expr_unit = self._infer_type(expr)
            if prop == "cant":
                if expr_type != "numero":
                    self.errores.append(f"Asignación a '{var}.cant' debe ser numérica, no {expr_type}")
                if simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
                    self.errores.append(f"Incompatibilidad de unidades: '{var}' usa {simbolo.info['unidad']}, expresión usa {expr_unit}")
            elif prop in ["temp", "presion"]:
                if expr_type != "numero":
                    self.errores.append(f"Asignación a '{var}.{prop}' debe ser numérica, no {expr_type}")
                expected_unit = "gradC" if prop == "temp" else "atm"
                if expr_unit != expected_unit:
                    self.errores.append(f"Incompatibilidad de unidades: '{prop}' requiere {expected_unit}, expresión usa {expr_unit}")
                # Verify if the property exists in metadatos or add it
                meta = simbolo.info.get("metadatos", [])
                found = False
                for v, u in meta:
                    if (prop == "temp" and u == "gradC") or (prop == "presion" and u == "atm"):
                        found = True
                        break
                if not found:
                    self.errores.append(f"Propiedad '{prop}' no definida para la sustancia '{var}'")
            else:
                self.errores.append(f"Propiedad desconocida '{prop}' para la sustancia '{var}'")
        else:
            name = target
            simbolo = self.tabla_simbolos.buscar(name)
            if not simbolo:
                self.errores.append(f"Variable '{name}' no declarada")
                return
            expr_type, expr_unit = self._infer_type(expr)
            if expr_type != simbolo.tipo:
                self.errores.append(f"Tipo incompatible en asignación: {name} es {simbolo.tipo}, expresión es {expr_type}")
            if simbolo.tipo == "sustancia" and simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
                self.errores.append(f"Incompatibilidad de unidades: {name} usa {simbolo.info['unidad']}, expresión usa {expr_unit}")

    def _verificar_reaccion(self, nodo):
        _, name, reactivos, productos, _ = nodo
        for _, param in reactivos + productos:
            simbolo = self.tabla_simbolos.buscar(param)
            if not simbolo or simbolo.tipo != "sustancia":
                self.errores.append(f"Parámetro '{param}' no es una sustancia válida")

    def _verificar_llamada(self, nodo):
        _, name, args = nodo
        simbolo = self.tabla_simbolos.buscar(name)
        if not simbolo or simbolo.tipo != "reaccion":
            self.errores.append(f"Reacción '{name}' no declarada")
            return

        expected = simbolo.info["reactivos"]
        if len(args) != len(expected):
            self.errores.append(f"Reacción '{name}' espera {len(expected)} argumentos, se proporcionaron {len(args)}")

    def _verificar_mezclar(self, nodo):
        _, expr, tgt = nodo
        expr_type, expr_unit = self._infer_type(expr)
        if expr_type != "sustancia":
            self.errores.append(f"Expresión en 'mezclar' debe ser sustancia, no {expr_type}")

        # Check or create symbol for target
        simbolo = self.tabla_simbolos.buscar(tgt)
        if not simbolo:
            simbolo = Simbolo(tgt, "sustancia", cantidad="0", unidad=None, metadatos=[])
            self.tabla_simbolos.insertar(tgt, simbolo)
        elif simbolo.tipo != "sustancia":
            self.errores.append(f"Destino '{tgt}' no es una sustancia válida")
            return
        elif simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
            self.errores.append(f"Incompatibilidad de unidades en 'mezclar': destino usa {simbolo.info['unidad']}, expresión usa {expr_unit}")

        # Propagar metadatos comunes al símbolo destino
        if isinstance(expr, tuple) and expr[0] == "BIN_OP" and expr[1] == "+":
            left, right = expr[2], expr[3]
            if left[0] == "VAR" and right[0] == "VAR":
                left_sim = self.tabla_simbolos.buscar(left[1])
                right_sim = self.tabla_simbolos.buscar(right[1])
                if left_sim and right_sim:
                    # Convertir metadatos a diccionarios {unidad: valor}
                    left_meta = dict((u, v) for v, u in left_sim.info.get("metadatos", []))
                    right_meta = dict((u, v) for v, u in right_sim.info.get("metadatos", []))
                    # Unidades comunes entre ambas sustancias
                    unidades_comunes = set(left_meta.keys()) & set(right_meta.keys())
                    # Crear metadatos dummy con valor "0" para evitar errores semánticos
                    nuevos_meta = [("0", u) for u in unidades_comunes]
                    simbolo.info["metadatos"] = nuevos_meta



    def _verificar_balancear(self, nodo):
        _, expr = nodo
        expr_type, _ = self._infer_type(expr)
        if expr_type != "sustancia":
            self.errores.append(f"Expresión en 'balancear' debe ser sustancia, no {expr_type}")

    def _verificar_mostrar(self, nodo):
        _, args = nodo
        for arg in args:
            if arg[0] == "TEXT":
                continue
            expr_type, _ = self._infer_type(arg)
            if expr_type not in ["sustancia", "numero", "cadena"]:
                self.errores.append(f"Argumento en 'mostrar' debe ser sustancia, número o cadena, no {expr_type}")

    def _verificar_control(self, nodo):
        tipo = nodo[0]
        if tipo == "SI":
            _, cond, _, _ = nodo
        else:
            _, cond, _ = nodo

        cond_type, _ = self._infer_type(cond)
        if cond_type != "booleano":
            self.errores.append(f"Condición en '{tipo}' debe ser booleana, no {cond_type}")

    def _infer_type(self, node):
        if isinstance(node, tuple):
            if node[0] == "VAR":
                simbolo = self.tabla_simbolos.buscar(node[1])
                if not simbolo:
                    return "desconocido", None
                return simbolo.tipo, simbolo.info.get("unidad")
            elif node[0] == "PROP_ACCESS":
                var, prop = node[1], node[2]
                simbolo = self.tabla_simbolos.buscar(var)
                if not simbolo or simbolo.tipo != "sustancia":
                    self.errores.append(f"'{var}' debe ser una sustancia para acceder a la propiedad '{prop}'")
                    return "desconocido", None
                if prop == "cant":
                    return "numero", simbolo.info.get("unidad")
                elif prop in ["temp", "presion"]:
                    for v, u in simbolo.info.get("metadatos", []):
                        if (prop == "temp" and u == "gradC") or (prop == "presion" and u == "atm"):
                            return "numero", u
                    self.errores.append(f"Propiedad '{prop}' no definida para la sustancia '{var}'")
                    return "desconocido", None
                else:
                    self.errores.append(f"Propiedad desconocida '{prop}' para la sustancia '{var}'")
                    return "desconocido", None
            elif node[0] == "NUM":
                return "numero", None
            elif node[0] == "TEXT":
                return "cadena", None
            elif node[0] == "BIN_OP":
                op, left, right = node[1], node[2], node[3]
                left_type, left_unit = self._infer_type(left)
                right_type, right_unit = self._infer_type(right)
                if op in ["+", "-"]:
                    if left_type == right_type == "sustancia":
                        if left_unit != right_unit:
                            self.errores.append(f"Incompatibilidad de unidades: {left_unit} y {right_unit}")
                        return "sustancia", left_unit
                    elif left_type == right_type == "cadena" and op == "+":
                        return "cadena", None
                    elif left_type == right_type == "numero":
                        return "numero", None
                    else:
                        self.errores.append(f"Operador '{op}' no válido entre tipos {left_type} y {right_type}")
                elif op in ["*", "/"]:
                    if left_type == "sustancia" and right_type == "numero":
                        return "sustancia", left_unit
                    elif left_type == right_type == "numero":
                        return "numero", None
                    else:
                        self.errores.append(f"Operador '{op}' no válido entre tipos {left_type} y {right_type}")
            elif node[0] == "COND":
                return "booleano", None
            elif node[0] == "LOGIC":
                return "booleano", None
        return "desconocido", None