from simbolos import *

class CodeGenerator:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.temp_count = 0
        self.label_count = 0
        self.polish = []
        self.pcode = []
        self.triples = []
        self.quads = []
        self.current_function = None

    def new_temp(self):
        temp = f"T{self.temp_count}"
        self.temp_count += 1
        return temp

    def new_label(self):
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def expr_to_notation(self, expr, notation="infix"):
        if not isinstance(expr, tuple):
            return str(expr)
        if expr[0] in ("VAR", "NUM", "TEXT"):
            return expr[1]
        if expr[0] == "BIN_OP":
            op, left, right = expr[1], expr[2], expr[3]
            L = self.expr_to_notation(left, notation)
            R = self.expr_to_notation(right, notation)
            if notation == "prefix":
                return f"{op} {L} {R}"
            elif notation == "postfix":
                return f"{L} {R} {op}"
            return f"({L} {op} {R})"
        return ""

    def generate(self, ast):
        self.polish = []
        self.pcode = []
        self.triples = []
        self.quads = []
        self.generate_stmt(ast)
        return {
            "polish": self.polish,
            "pcode": self.pcode,
            "triples": self.triples,
            "quads": self.quads
        }

    def generate_stmt(self, node):
        if not isinstance(node, tuple):
            return
        node_type = node[0]

        if node_type == "PROGRAM":
            for stmt in node[1]:
                self.generate_stmt(stmt)

        elif node_type == "SUSTANCIA":
            name, qty, unit, meta = node[1], node[2], node[3], node[4]
            self.polish.append(f"DECLARE sustancia {name} = {qty}{unit or ''}")
            self.pcode.append(f"DECL {name} sustancia")
            self.triples.append((len(self.triples), "DECL", name, f"{qty}{unit or ''}"))
            self.quads.append((len(self.quads), "DECL", name, f"{qty}{unit or ''}", None))
            if meta:
                for v, u in meta:
                    self.polish.append(f"META {name} {v}{u}")
                    self.pcode.append(f"META {name} {v}{u}")
                    self.triples.append((len(self.triples), "META", name, f"{v}{u}"))
                    self.quads.append((len(self.quads), "META", name, f"{v}{u}", None))

        elif node_type == "NUMERO":
            name, expr = node[1], node[2]
            result = self.generate_expr(expr)
            self.polish.append(f"DECLARE numero {name} = {result}")
            self.pcode.append(f"DECL {name} numero")
            self.pcode.append(f"STO {name} {result}")
            self.triples.append((len(self.triples), "DECL", name, "numero"))
            self.triples.append((len(self.triples), "=", name, result))
            self.quads.append((len(self.quads), "DECL", name, "numero", None))
            self.quads.append((len(self.quads), "=", name, result, None))

        elif node_type == "CADENA":
            name, value = node[1], node[2]
            self.polish.append(f"DECLARE cadena {name} = {value}")
            self.pcode.append(f"DECL {name} cadena")
            self.pcode.append(f"STO {name} {value}")
            self.triples.append((len(self.triples), "DECL", name, "cadena"))
            self.triples.append((len(self.triples), "=", name, value))
            self.quads.append((len(self.quads), "DECL", name, "cadena", None))
            self.quads.append((len(self.quads), "=", name, value, None))

        elif node_type == "ASIGNACION":
            target, expr = node[1], node[2]
            result = self.generate_expr(expr)
            if isinstance(target, tuple) and target[0] == "PROP_ACCESS":
                var, prop = target[1], target[2]
                self.polish.append(f"{var}.{prop} = {result}")
                self.pcode.append(f"SET_PROP {var} {prop} {result}")
                self.triples.append((len(self.triples), "SET_PROP", var, prop, result))
                self.quads.append((len(self.quads), "SET_PROP", var, prop, result))
            else:
                name = target
                self.polish.append(f"{name} = {result}")
                self.pcode.append(f"STO {name} {result}")
                if not result.isdigit():
                    self.triples.append((len(self.triples), "=", name, result))
                    self.quads.append((len(self.quads), "=", name, result, None))

        elif node_type == "EXPRESSION":
            self.generate_expr(node[1])

        elif node_type == "DEF_REACCION":
            name, reactivos, productos, body = node[1], node[2], node[3], node[4]
            self.current_function = name
            self.polish.append(f"FUNCTION {name}({','.join(f'{c}{n}' for c,n in reactivos)} -> {','.join(f'{c}{n}' for c,n in productos)})")
            self.pcode.append(f"FUNC {name}")
            self.triples.append((len(self.triples), "FUNC", name, None))
            self.quads.append((len(self.quads), "FUNC", name, None, None))
            self.generate_stmt(body)
            self.polish.append("END_FUNCTION")
            self.pcode.append("END")
            self.triples.append((len(self.triples), "END", None, None))
            self.quads.append((len(self.quads), "END", None, None, None))
            self.current_function = None
        elif node_type == "CALL":
            name, args = node[1], node[2]
            arg_str = ','.join(f'{c}{n}' for c,n in args)
            self.polish.append(f"CALL {name}({arg_str})")
            self.pcode.append(f"CALL {name} {arg_str}")
            self.triples.append((len(self.triples), "CALL", name, arg_str))
            self.quads.append((len(self.quads), "CALL", name, arg_str, None))
        elif node_type == "MEZCLAR":
            expr, tgt = node[1], node[2]
            result = self.generate_expr(expr)
            self.polish.append(f"MEZCLAR {result} -> {tgt}")
            self.pcode.append(f"MIX {result} {tgt}")
            self.triples.append((len(self.triples), "MIX", result, tgt))
            self.quads.append((len(self.quads), "MIX", result, tgt, None))
            # Add metadata handling for binary operations
            if isinstance(expr, tuple) and expr[0] == "BIN_OP" and expr[1] == "+":
                left, right = expr[2], expr[3]
                if left[0] == "VAR" and right[0] == "VAR":
                    left_var, right_var = left[1], right[1]
                    # Generate code for metadata (temp and presion)
                    for prop in ["temp", "presion"]:
                        temp = self.new_temp()
                        self.polish.append(f"{temp} = AVG({left_var}.{prop}, {right_var}.{prop})")
                        self.pcode.append(f"AVG_PROP {left_var} {right_var} {prop} {temp}")
                        self.triples.append((len(self.triples), "AVG_PROP", f"{left_var}.{prop}", f"{right_var}.{prop}"))
                        self.quads.append((len(self.quads), "AVG_PROP", f"{left_var}.{prop}", f"{right_var}.{prop}", temp))
                        self.polish.append(f"SET {tgt}.{prop} = {temp}")
                        self.pcode.append(f"SET_PROP {tgt} {prop} {temp}")
                        self.triples.append((len(self.triples), "SET_PROP", tgt, prop, temp))
                        self.quads.append((len(self.quads), "SET_PROP", tgt, prop, temp))
        elif node_type == "BALANCEAR":
            expr = node[1]
            result = self.generate_expr(expr)
            self.polish.append(f"BALANCEAR {result}")
            self.pcode.append(f"BAL {result}")
            self.triples.append((len(self.triples), "BAL", result, None))
            self.quads.append((len(self.quads), "BAL", result, None, None))
        elif node_type == "MOSTRAR":
            args = node[1]
            arg_results = [self.generate_expr(arg) if arg[0] not in ["TEXT"] else arg[1] for arg in args]
            arg_str = ','.join(arg_results)
            self.polish.append(f"MOSTRAR {arg_str}")
            self.pcode.append(f"PRINT {arg_str}")
            self.triples.append((len(self.triples), "PRINT", arg_str, None))
            self.quads.append((len(self.quads), "PRINT", arg_str, None, None))
        elif node_type == "SI":
            cond, then_block, else_block = node[1], node[2], node[3]
            cond_result = self.generate_cond(cond)
            then_label = self.new_label()
            end_label = self.new_label()
            else_label = self.new_label() if else_block else end_label
            self.polish.append(f"IF {cond_result} GOTO {then_label}")
            self.pcode.append(f"JMP_IF {cond_result} {then_label}")
            self.triples.append((len(self.triples), "JMP_IF", cond_result, then_label))
            self.quads.append((len(self.quads), "JMP_IF", cond_result, then_label, None))
            self.polish.append(f"GOTO {else_label}")
            self.pcode.append(f"JMP {else_label}")
            self.triples.append((len(self.triples), "JMP", else_label, None))
            self.quads.append((len(self.quads), "JMP", else_label, None, None))
            self.polish.append(f"{then_label}:")
            self.pcode.append(f"{then_label}:")
            self.triples.append((len(self.triples), "LABEL", then_label, None))
            self.quads.append((len(self.quads), "LABEL", then_label, None, None))
            self.generate_stmt(then_block)
            if else_block:
                self.polish.append(f"GOTO {end_label}")
                self.pcode.append(f"JMP {end_label}")
                self.triples.append((len(self.triples), "JMP", end_label, None))
                self.quads.append((len(self.quads), "JMP", end_label, None, None))
                self.polish.append(f"{else_label}:")
                self.pcode.append(f"{else_label}:")
                self.triples.append((len(self.triples), "LABEL", else_label, None))
                self.quads.append((len(self.quads), "LABEL", else_label, None, None))
                self.generate_stmt(else_block)
            self.polish.append(f"{end_label}:")
            self.pcode.append(f"{end_label}:")
            self.triples.append((len(self.triples), "LABEL", end_label, None))
            self.quads.append((len(self.quads), "LABEL", end_label, None, None))
        elif node_type == "REPETIR_HASTA":
            cond, body = node[1], node[2]
            start_label = self.new_label()
            end_label = self.new_label()
            self.polish.append(f"{start_label}:")
            self.pcode.append(f"{start_label}:")
            self.triples.append((len(self.triples), "LABEL", start_label, None))
            self.quads.append((len(self.quads), "LABEL", start_label, None, None))
            self.generate_stmt(body)
            cond_result = self.generate_cond(cond)
            self.polish.append(f"IF_NOT {cond_result} GOTO {start_label}")
            self.pcode.append(f"JMP_IF_NOT {cond_result} {start_label}")
            self.triples.append((len(self.triples), "JMP_IF_NOT", cond_result, start_label))
            self.quads.append((len(self.quads), "JMP_IF_NOT", cond_result, start_label, None))
            self.polish.append(f"{end_label}:")
            self.pcode.append(f"{end_label}:")
            self.triples.append((len(self.triples), "LABEL", end_label, None))
            self.quads.append((len(self.quads), "LABEL", end_label, None, None))
        elif node_type == "HACER_MIENTRAS":
            cond, body = node[1], node[2]
            start_label = self.new_label()
            end_label = self.new_label()
            self.polish.append(f"{start_label}:")
            self.pcode.append(f"{start_label}:")
            self.triples.append((len(self.triples), "LABEL", start_label, None))
            self.quads.append((len(self.quads), "LABEL", start_label, None, None))
            cond_result = self.generate_cond(cond)
            self.polish.append(f"IF_NOT {cond_result} GOTO {end_label}")
            self.pcode.append(f"JMP_IF_NOT {cond_result} {end_label}")
            self.triples.append((len(self.triples), "JMP_IF_NOT", cond_result, end_label))
            self.quads.append((len(self.quads), "JMP_IF_NOT", cond_result, end_label, None))
            self.generate_stmt(body)
            self.polish.append(f"GOTO {start_label}")
            self.pcode.append(f"JMP {start_label}")
            self.triples.append((len(self.triples), "JMP", start_label, None))
            self.quads.append((len(self.quads), "JMP", start_label, None, None))
            self.polish.append(f"{end_label}:")
            self.pcode.append(f"{end_label}:")
            self.triples.append((len(self.triples), "LABEL", end_label, None))
            self.quads.append((len(self.quads), "LABEL", end_label, None, None))
        elif node_type == "DETENER":
            self.polish.append("BREAK")
            self.pcode.append("BRK")
            self.triples.append((len(self.triples), "BRK", None, None))
            self.quads.append((len(self.quads), "BRK", None, None, None))
        elif node_type == "BLOQUE":
            for stmt in node[1]:
                self.generate_stmt(stmt)
        elif node_type == "COMMENT":
            self.polish.append(f"// {node[1]}")
            self.pcode.append(f"// {node[1]}")
            self.triples.append((len(self.triples), "COMMENT", node[1], None))
            self.quads.append((len(self.quads), "COMMENT", node[1], None, None))

    def generate_expr(self, expr):
        if expr[0] == "VAR":
            return expr[1]
        if expr[0] == "NUM":
            return expr[1]
        if expr[0] == "TEXT":
            return expr[1]
        if expr[0] == "PROP_ACCESS":
            var, prop = expr[1], expr[2]
            temp = self.new_temp()
            self.polish.append(f"{temp} = {var}.{prop}")
            self.pcode.append(f"GET_PROP {var} {prop} {temp}")
            self.triples.append((len(self.triples), "GET_PROP", var, prop))
            self.quads.append((len(self.quads), "GET_PROP", var, prop, temp))
            return temp
        if expr[0] == "BIN_OP":
            op, left, right = expr[1], expr[2], expr[3]
            L = self.generate_expr(left)
            R = self.generate_expr(right)
            idx = len(self.triples)
            self.triples.append((idx, op, L, R))
            self.quads.append((idx, op, L, R, None))
            if left[0] == right[0] == "NUM":
                try:
                    v = eval(f"{L} {op} {R}")
                    if isinstance(v, float) and v.is_integer():
                        v = int(v)
                    return str(v)
                except Exception:
                    pass
            temp = self.new_temp()
            polish_str = self.expr_to_notation(expr, "prefix")
            self.polish.append(f"{temp} = {polish_str}")
            self.pcode.append(f"OP {op} {L} {R} {temp}")
            return temp
        return ""

    def generate_cond(self, cond):
        if cond[0] == "COND":
            op, left, right = cond[1], cond[2], cond[3]
            left_result = self.generate_expr(left)
            right_result = self.generate_expr(right)
            temp = self.new_temp()
            self.polish.append(f"{temp} = {left_result} {op} {right_result}")
            self.pcode.append(f"CMP {op} {left_result} {right_result} {temp}")
            self.triples.append((len(self.triples), op, left_result, right_result))
            self.quads.append((len(self.quads), op, left_result, right_result, temp))
            return temp
        elif cond[0] == "LOGIC":
            op, left, right = cond[1], cond[2], cond[3]
            left_result = self.generate_cond(left)
            right_result = self.generate_cond(right)
            temp = self.new_temp()
            self.polish.append(f"{temp} = {left_result} {op} {right_result}")
            self.pcode.append(f"LOG {op} {left_result} {right_result} {temp}")
            self.triples.append((len(self.triples), op, left_result, right_result))
            self.quads.append((len(self.quads), op, left_result, right_result, temp))
            return temp
        return ""