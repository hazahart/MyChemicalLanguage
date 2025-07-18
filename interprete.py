import re
from mcl_tokens import *
from simbolos import Simbolo
from decimal import Decimal, InvalidOperation

class Interprete:
    def __init__(self, ast, tabla_simbolos):
        self.ast = ast
        self.tabla_simbolos = tabla_simbolos
        self.resultados = []
        self.variables = {}
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
                self.variables[name] = {"cantidad": qty, "unidad": unit, "metadatos": meta}
                print(f"DEBUG: Declarada sustancia '{name}' con cantidad {qty}, unidad {unit}, meta {meta}")
            except InvalidOperation:
                self.errores.append(f"Cantidad inválida para sustancia '{name}': {qty}")

        elif tipo == "NUMERO":
            name, expr = nodo[1], nodo[2]
            valor = self._evaluar_expr(expr)
            if valor is not None:
                self.variables[name] = {"valor": valor}

        elif tipo == "CADENA":
            name, value = nodo[1], nodo[2]
            value = value[1:-1] if value.startswith('"') and value.endswith('"') else value
            self.variables[name] = {"valor": value}

        elif tipo == "ASIGNACION":
            target, expr = nodo[1], nodo[2]
            valor = self._evaluar_expr(expr)
            if valor is None:
                return
            if isinstance(target, tuple) and target[0] == "PROP_ACCESS":
                var, prop = target[1], target[2]
                if var not in self.variables:
                    self.errores.append(f"Variable '{var}' no declarada")
                    return
                if prop == "cant":
                    self.variables[var]["cantidad"] = valor
                elif prop in ["temp", "presion"]:
                    expected_unit = "gradC" if prop == "temp" else "atm"
                    meta = self.variables[var].get("metadatos", [])
                    new_meta = [(v, u) for v, u in meta if u != expected_unit]
                    new_meta.append((str(valor), expected_unit))
                    self.variables[var]["metadatos"] = new_meta
                else:
                    self.errores.append(f"Propiedad desconocida '{prop}' para '{var}'")
                    return
            else:
                name = target
                if name in self.variables:
                    self.variables[name]["valor"] = valor
                else:
                    self.errores.append(f"Variable '{name}' no declarada")

        elif tipo == "DEF_REACCION":
            name, reactivos, productos, cuerpo = nodo[1], nodo[2], nodo[3], nodo[4]
            self.variables[name] = {"tipo": "reaccion", "reactivos": reactivos, "productos": productos, "cuerpo": cuerpo}

        elif tipo == "CALL":
            name, args = nodo[1], nodo[2]
            reaccion = self.variables.get(name)
            if not reaccion or reaccion["tipo"] != "reaccion":
                self.errores.append(f"Reacción '{name}' no definida")
                return
            expected = [(coeff, n) for coeff, n in reaccion["reactivos"]]
            if len(args) != len(expected):
                self.errores.append(f"Reacción '{name}' espera {len(expected)} argumentos, se dieron {len(args)}")
                return
            for (c1, n1), (c2, n2) in zip(expected, args):
                if n1 != n2 or c1 != c2:
                    self.errores.append(f"Reactivo esperado: {c1}{n1}, encontrado: {c2}{n2}")
                    return
            self.tabla_simbolos.entrar_bloque()
            for coeff, param in args:
                if param in self.variables:
                    self.tabla_simbolos.insertar(param, Simbolo(param, "sustancia", cantidad=str(self.variables[param]["cantidad"]), unidad=self.variables[param]["unidad"]))
            self._ejecutar_nodo(reaccion["cuerpo"])
            self.tabla_simbolos.salir_bloque()

        elif tipo == "MEZCLAR":
            expr, tgt = nodo[1], nodo[2]
            print(f"DEBUG: Procesando MEZCLAR con expr {expr}, target {tgt}")
            # Handle substance combination directly
            if isinstance(expr, tuple) and expr[0] == "BIN_OP" and expr[1] == "+":
                left, right = expr[2], expr[3]
                if left[0] == "VAR" and right[0] == "VAR":
                    left_var, right_var = left[1], right[1]
                    if left_var not in self.variables or right_var not in self.variables:
                        self.errores.append(f"Variable no definida: {left_var} o {right_var}")
                        return
                    # Initialize target if not declared
                    if tgt not in self.variables:
                        self.variables[tgt] = {"cantidad": Decimal('0'), "unidad": None, "metadatos": []}
                        self.tabla_simbolos.insertar(tgt, Simbolo(tgt, "sustancia", cantidad="0", unidad=None, metadatos=[]))
                    # Combine quantities
                    left_qty = self.variables[left_var]["cantidad"]
                    right_qty = self.variables[right_var]["cantidad"]
                    total_qty = left_qty + right_qty
                    self.variables[tgt]["cantidad"] = total_qty
                    # Inherit unit from first substance if consistent
                    if self.variables[left_var]["unidad"] and self.variables[right_var]["unidad"]:
                        if self.variables[left_var]["unidad"] != self.variables[right_var]["unidad"]:
                            self.errores.append(f"Incompatibilidad de unidades: {left_var} usa {self.variables[left_var]['unidad']}, {right_var} usa {self.variables[right_var]['unidad']}")
                            return
                        self.variables[tgt]["unidad"] = self.variables[left_var]["unidad"]
                    elif self.variables[left_var]["unidad"]:
                        self.variables[tgt]["unidad"] = self.variables[left_var]["unidad"]
                    # Combine metadata with default values for missing properties
                    left_meta = dict((u, v) for v, u in self.variables[left_var].get("metadatos", []))
                    right_meta = dict((u, v) for v, u in self.variables[right_var].get("metadatos", []))
                    new_meta = []
                    # Handle temperature (gradC)
                    left_temp = Decimal(left_meta.get("gradC", "0"))
                    right_temp = Decimal(right_meta.get("gradC", "0"))
                    avg_temp = (left_temp * left_qty + right_temp * right_qty) / total_qty
                    new_meta.append((str(avg_temp), "gradC"))
                    # Handle pressure (atm)
                    left_pres = Decimal(left_meta.get("atm", "0"))
                    right_pres = Decimal(right_meta.get("atm", "0"))
                    avg_pres = (left_pres * left_qty + right_pres * right_qty) / total_qty
                    new_meta.append((str(avg_pres), "atm"))
                    self.variables[tgt]["metadatos"] = new_meta
                    self.tabla_simbolos.buscar(tgt).info["metadatos"] = new_meta
                    print(f"DEBUG: Mezcla completada, {tgt} tiene cantidad {self.variables[tgt]['cantidad']}, meta {new_meta}")
            else:
                valor = self._evaluar_expr(expr)
                if valor is None:
                    return
                if tgt not in self.variables:
                    self.variables[tgt] = {"cantidad": Decimal('0'), "unidad": None, "metadatos": []}
                    self.tabla_simbolos.insertar(tgt, Simbolo(tgt, "sustancia", cantidad="0", unidad=None, metadatos=[]))
                if "cantidad" not in self.variables[tgt]:
                    self.errores.append(f"Destino '{tgt}' no es una sustancia válida")
                    return
                self.variables[tgt]["cantidad"] += valor
                expr_type, expr_unit = self._infer_type(expr)
                if expr_unit and self.variables[tgt]["unidad"] is None:
                    self.variables[tgt]["unidad"] = expr_unit
                elif expr_unit and self.variables[tgt]["unidad"] != expr_unit:
                    self.errores.append(f"Incompatibilidad de unidades: destino '{tgt}' usa {self.variables[tgt]['unidad']}, expresión usa {expr_unit}")
                    return
        elif tipo == "BALANCEAR":
            expr = nodo[1]
            valor = self._evaluar_expr(expr)
            if valor is None:
                return
            # Simular balanceo
            self.variables[f"balanced_{expr[1]}"] = {"cantidad": valor}

        elif tipo == "MOSTRAR":
            args = nodo[1]
            print(f"DEBUG: Procesando MOSTRAR con args {args}")
            output = []
            for arg in args:
                if arg[0] == "TEXT":
                    output.append(arg[1][1:-1] if arg[1].startswith('"') and arg[1].endswith('"') else arg[1])
                else:
                    valor = self._evaluar_expr(arg)
                    if valor is not None:
                        output.append(str(valor))
                    else:
                        print(f"DEBUG: Valor nulo para {arg}")
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
                print(f"DEBUG: Evaluando '{name}' desde variables: {self.variables[name]}")
                return self.variables[name].get("valor", self.variables[name].get("cantidad"))
            simbolo = self.tabla_simbolos.buscar(name)
            if simbolo and "valor" in simbolo.info:
                return Decimal(str(simbolo.info["valor"]))
            self.errores.append(f"Variable '{name}' no inicializada")
            return None
        elif expr[0] == "PROP_ACCESS":
            var, prop = expr[1], expr[2]
            if var not in self.variables:
                self.errores.append(f"Variable '{var}' no definida")
                return None
            print(f"DEBUG: Accediendo a '{prop}' de '{var}', metadatos: {self.variables[var].get('metadatos', [])}")
            if prop == "cant":
                if "cantidad" in self.variables[var]:
                    return self.variables[var]["cantidad"]
                self.errores.append(f"Sustancia '{var}' no tiene cantidad definida")
                return None
            elif prop in ["temp", "presion"]:
                expected_unit = "gradC" if prop == "temp" else "atm"
                meta = self.variables[var].get("metadatos", [])
                for value, unit in meta:
                    if unit == expected_unit:
                        print(f"DEBUG: Encontrado '{prop}' = {value} {unit} para '{var}'")
                        return Decimal(value)
                print(f"DEBUG: Propiedad '{prop}' no encontrada en '{var}', usando 0 {expected_unit}")
                return Decimal('0')
            else:
                self.errores.append(f"Propiedad desconocida '{prop}' para '{var}'")
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
            if op == "+" and isinstance(left_val, Decimal) and isinstance(right_val, Decimal):
                return left_val + right_val
            elif op == "+" and left[0] == "VAR" and right[0] == "VAR":
                print(f"DEBUG: Deferring '{left[1]} + {right[1]}' to MEZCLAR")
                return None
            try:
                if op == "-":
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
            elif node[0] == "PROP_ACCESS":
                var, prop = node[1], node[2]
                simbolo = self.tabla_simbolos.buscar(var)
                if not simbolo or simbolo.tipo != "sustancia":
                    self.errores.append(f"'{var}' debe ser una sustancia para acceder a la propiedad '{prop}'")
                    return "desconocido", None
                if prop == "cant":
                    return "numero", simbolo.info.get("unidad")
                elif prop in ["temp", "presion"]:
                    expected_unit = "gradC" if prop == "temp" else "atm"
                    return "numero", expected_unit
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
                if op == "+" and left_type == right_type == "sustancia":
                    if left_unit != right_unit:
                        self.errores.append(f"Incompatibilidad de unidades: {left_unit} y {right_unit}")
                    return "sustancia", left_unit
                elif op == "+" and left_type == right_type == "numero":
                    return "numero", None
                elif op == "+" and left_type == right_type == "cadena":
                    return "cadena", None
                elif op in ["*", "/"] and left_type == "numero" and right_type == "numero":
                    return "numero", None
                self.errores.append(f"Operación '{op}' no válida entre {left_type} y {right_type}")
                return "desconocido", None
        return "desconocido", None
    
    def get_resultados(self):
        return self.resultados

    def get_errores(self):
        return self.errores