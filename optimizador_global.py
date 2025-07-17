# optimizador_global.py
from mcl_tokens import *

class OptimizadorGlobal:
    def __init__(self, ast):
        self.ast = ast
        self.consts = {}

    def optimizar(self):
        ast1 = self._fold_ast(self.ast)
        self.consts.clear()
        self._collect_consts(ast1)
        ast2 = self._propagate_consts(ast1)
        ast3 = self._fold_ast(ast2)
        return ast3

    def _fold_ast(self, nodo):
        # Si es lista, recórrela y repliega cada elemento
        if isinstance(nodo, list):
            return [self._fold_ast(x) for x in nodo]

        # Si no es tupla, devuélvelo tal cual
        if not isinstance(nodo, tuple):
            return nodo

        head = nodo[0]
        # Si es declaración "ASIGNACION" o "NUMERO", pliega su expr
        if head in ("ASIGNACION", "NUMERO"):
            name, expr = nodo[1], nodo[2]
            expr2 = self._fold_expr(expr)
            return (head, name, expr2)

        # Para cualquier otro nodo tupla, reconstruye recursivamente
        return tuple([head] + [self._fold_ast(child) for child in nodo[1:]])

    def _fold_expr(self, expr):
        if not isinstance(expr, tuple):
            return expr
        if expr[0] == "BIN_OP":
            op, left, right = expr[1], expr[2], expr[3]
            l2 = self._fold_expr(left)
            r2 = self._fold_expr(right)
            if l2[0] == r2[0] == "NUM":
                try:
                    v = eval(f"{l2[1]} {op} {r2[1]}")
                    if isinstance(v, float) and v.is_integer():
                        v = int(v)
                    return ("NUM", str(v))
                except:
                    pass
            return ("BIN_OP", op, l2, r2)
        return expr

    # Recolectar constantes de asignaciones/literales
    def _collect_consts(self, nodo):
        if isinstance(nodo, tuple):
            head = nodo[0]
            if head in ("ASIGNACION", "NUMERO"):
                name, expr = nodo[1], nodo[2]
                if isinstance(expr, tuple) and expr[0] == "NUM":
                    self.consts[name] = expr[1]
            for child in nodo[1:]:
                self._collect_consts(child)
        elif isinstance(nodo, list):
            for elem in nodo:
                self._collect_consts(elem)

    # Constant Propagation
    def _propagate_consts(self, nodo):
        # Lista → propaga en cada elemento
        if isinstance(nodo, list):
            return [self._propagate_consts(x) for x in nodo]

        # Sólo trata tuplas
        if not isinstance(nodo, tuple):
            return nodo

        head = nodo[0]
        # Si es uso de variable, reemplaza por NUM si existe
        if head == "VAR" and nodo[1] in self.consts:
            return ("NUM", self.consts[nodo[1]])

        # Reconstruye el nodo tupla con hijos propagados
        return tuple([head] + [self._propagate_consts(child) for child in nodo[1:]])