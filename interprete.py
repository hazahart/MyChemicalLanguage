import re
from mcl_tokens import *
from simbolos import Simbolo
from decimal import Decimal, InvalidOperation

class Interprete:
    def __init__(self, ast, tabla_simbolos):
        self.ast = ast
        self.tabla_simbolos = tabla_simbolos
        self.resultados = []  # To store output (e.g., from mostrar)
        self.variables = {}  # Runtime values for variables
        self.errores = []

    def ejecutar(self):
        try:
            self._ejecutar_nodo(self.ast)
            return self.resultados, self.errores
        except Exception as e:
            self.errores.append(f"Error en ejecución: {str(e)}")
            return self.resultados, self.errores

    def _ejecutar_nodo(self, nodo):
        if not isinstance(nodo, tuple):
            return
        tipo = nodo[0]

        if tipo == "PROGRAM":
            for stmt in nodo[1]:
                self._ejecutar_nodo(stmt)

        elif tipo == "SUSTANCIA":
            name, qty, unit, meta = nodo[1], nodo[2], nodo[3], nodo[4]
            try:
                qty = Decimal(qty)
                self.variables[name] = {"valor": qty, "unidad": unit, "metadatos": meta}
            except InvalidOperation:
                self.errores.append(f"Cantidad inválida para sustancia '{name}': {qty}")

        elif tipo == "NUMERO":
            name, expr = nodo[1], nodo[2]
            valor = self._evaluar_expr(expr)
            if valor is not None:
                self.variables[name] = {"valor": valor, "unidad": None}

        elif tipo == "CADENA":
            name, value = nodo[1], nodo[2]
            # Remove quotes for string value
            value = value[1:-1] if value.startswith('"') and value.endswith('"') else value
            self.variables[name] = {"valor": value, "unidad": None}

        elif tipo == "ASIGNACION":
            name, expr = nodo[1], nodo[2]
            valor = self._evaluar_expr(expr)
            if valor is not None:
                simbolo = self.tabla_simbolos.buscar(name)
                if simbolo:
                    if simbolo.tipo == "sustancia":
                        expr_type, expr_unit = self._infer_type(expr)
                        if expr_type != "sustancia":
                            self.errores.append(f"Asignación a '{name}' debe ser sustancia, no {expr_type}")
                            return
                        if simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
                            self.errores.append(f"Incompatibilidad de unidades en asignación a '{name}': {simbolo.info['unidad']} vs {expr_unit}")
                            return
                    self.variables[name] = {"valor": valor, "unidad": expr_unit if simbolo.tipo == "sustancia" else None}

        elif tipo == "DEF_REACCION":
            name, reactivos, productos, cuerpo = nodo[1], nodo[2], nodo[3], nodo[4]
            self.variables[name] = {"tipo": "reaccion", "reactivos": reactivos, "productos": productos, "cuerpo": cuerpo}

        elif tipo == "CALL":
            name, args = nodo[1], nodo[2]
            reaccion = self.variables.get(name)
            if not reaccion or reaccion["tipo"] != "reaccion":
                self.errores.append(f"Reacción '{name}' no definida")
                return
            # Validate arguments
            expected = [(coeff, n) for coeff, n in reaccion["reactivos"]]
            if len(args) != len(expected):
                self.errores.append(f"Reacción '{name}' espera {len(expected)} argumentos, se dieron {len(args)}")
                return
            for (c1, n1), (c2, n2) in zip(expected, args):
                if n1 != n2 or c1 != c2:
                    self.errores.append(f"Reactivo esperado: {c1}{n1}, encontrado: {c2}{n2}")
                    return
            # Execute reaction body with arguments
            self.tabla_simbolos.entrar_bloque()
            for coeff, param in args:
                simbolo = self.tabla_simbolos.buscar(param)
                if simbolo and param in self.variables:
                    self.tabla_simbolos.insertar(param, Simbolo(param, "sustancia", cantidad=str(self.variables[param]["valor"]), unidad=self.variables[param]["unidad"]))
            self._ejecutar_nodo(reaccion["cuerpo"])
            self.tabla_simbolos.salir_bloque()

        elif tipo == "MEZCLAR":
            expr, tgt = nodo[1], nodo[2]
            valor = self._evaluar_expr(expr)
            if valor is None:
                return
            simbolo = self.tabla_simbolos.buscar(tgt)
            if not simbolo or simbolo.tipo != "sustancia":
                self.errores.append(f"Destino '{tgt}' no es una sustancia válida")
                return
            expr_type, expr_unit = self._infer_type(expr)
            if expr_type != "sustancia":
                self.errores.append(f"Expresión en 'mezclar' debe ser sustancia, no {expr_type}")
                return
            if simbolo.info.get("unidad") and expr_unit and simbolo.info["unidad"] != expr_unit:
                self.errores.append(f"Incompatibilidad de unidades en 'mezclar' a '{tgt}': {simbolo.info['unidad']} vs {expr_unit}")
                return
            self.variables[tgt] = {"valor": valor, "unidad": expr_unit}

        elif tipo == "BALANCEAR":
            expr = nodo[1]
            valor = self._evaluar_expr(expr)
            if valor is None:
                return
            expr_type, _ = self._infer_type(expr)
            if expr_type != "sustancia":
                self.errores.append(f"Expresión en 'balancear' debe ser sustancia, no {expr_type}")
                return
            # Simulate balancing (for now, just store the value)
            self.variables[f"balanced_{expr[1]}"] = {"valor": valor, "unidad": None}

        elif tipo == "MOSTRAR":
            args = nodo[1]
            output = []
            for arg in args:
                if arg[0] == "TEXT":
                    output.append(arg[1][1:-1] if arg[1].startswith('"') and arg[1].endswith('"') else arg[1])
                else:
                    valor = self._evaluar_expr(arg)
                    if valor is not None:
                        output.append(str(valor))
            self.resultados.append(" ".join(output))

        elif tipo == "SI":
            cond, then_block, else_block = nodo[1], nodo[2], nodo[3]
            if self._evaluar_cond(cond):
                self._ejecutar_nodo(then_block)
            elif else_block:
                self._ejecutar_nodo(else_block)

        elif tipo == "REPETIR_HASTA":
            cond, cuerpo = nodo[1], nodo[2]
            while not self._evaluar_cond(cond):
                self._ejecutar_nodo(cuerpo)

        elif tipo == "HACER_MIENTRAS":
            cond, cuerpo = nodo[1], nodo[2]
            while True:
                self._ejecutar_nodo(cuerpo)
                if not self._evaluar_cond(cond):
                    break

        elif tipo == "DETENER":
            # Break from the current loop (handled by caller)
            raise StopIteration

        elif tipo == "BLOQUE":
            self.tabla_simbolos.entrar_bloque()
            for stmt in nodo[1]:
                try:
                    self._ejecutar_nodo(stmt)
                except StopIteration:
                    break
            self.tabla_simbolos.salir_bloque()

    def _evaluar_expr(self, expr):
        if not isinstance(expr, tuple):
            return None
        if expr[0] == "VAR":
            name = expr[1]
            if name in self.variables:
                return self.variables[name]["valor"]
            simbolo = self.tabla_simbolos.buscar(name)
            if simbolo and "valor" in simbolo.info:
                return Decimal(str(simbolo.info["valor"]))
            self.errores.append(f"Variable '{name}' no inicializada")
            return None
        elif expr[0] == "NUM":
            try:
                return Decimal(expr[1])
            except InvalidOperation:
                self.errores.append(f"Número inválido: {expr[1]}")
                return None
        elif expr[0] == "TEXT":
            return expr[1][1:-1] if expr[1].startswith('"') and expr[1].endswith('"') else expr[1]
        elif expr[0] == "BIN_OP":
            op, left, right = expr[1], expr[2], expr[3]
            left_val = self._evaluar_expr(left)
            right_val = self._evaluar_expr(right)
            if left_val is None or right_val is None:
                return None
            try:
                if op == "+":
                    return left_val + right_val
                elif op == "-":
                    return left_val - right_val
                elif op == "*":
                    return left_val * right_val
                elif op == "/":
                    if right_val == 0:
                        self.errores.append("División por cero")
                        return None
                    return left_val / right_val
            except InvalidOperation:
                self.errores.append(f"Operación inválida: {left_val} {op} {right_val}")
                return None
        return None

    def _evaluar_cond(self, cond):
        if cond[0] == "COND":
            op, left, right = cond[1], cond[2], cond[3]
            left_val = self._evaluar_expr(left)
            right_val = self._evaluar_expr(right)
            if left_val is None or right_val is None:
                return False
            try:
                if op == "==":
                    return left_val == right_val
                elif op == "!=":
                    return left_val != right_val
                elif op == "<":
                    return left_val < right_val
                elif op == ">":
                    return left_val > right_val
                elif op == "<=":
                    return left_val <= right_val
                elif op == ">=":
                    return left_val >= right_val
            except InvalidOperation:
                self.errores.append(f"Comparación inválida: {left_val} {op} {right_val}")
                return False
        elif cond[0] == "LOGIC":
            op, left, right = cond[1], cond[2], cond[3]
            left_val = self._evaluar_cond(left)
            right_val = self._evaluar_cond(right)
            if op == "y":
                return left_val and right_val
            elif op == "o":
                return left_val or right_val
        return False

    def _infer_type(self, node):
        if isinstance(node, tuple):
            if node[0] == "VAR":
                simbolo = self.tabla_simbolos.buscar(node[1])
                if not simbolo:
                    return "desconocido", None
                return simbolo.tipo, simbolo.info.get("unidad")
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
                            self.errores.append(f"Incompatibilidad de unidades: {left_unit} vs {right_unit}")
                        return "sustancia", left_unit
                    elif left_type == right_type == "cadena" and op == "+":
                        return "cadena", None
                    elif left_type == right_type == "numero":
                        return "numero", None
                elif op in ["*", "/"]:
                    if left_type == "sustancia" and right_type == "numero":
                        return "sustancia", left_unit
                    elif left_type == right_type == "numero":
                        return "numero", None
        return "desconocido", None