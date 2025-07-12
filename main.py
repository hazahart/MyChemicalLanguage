import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from analizador_lexico import AFD_Lexico
from analizador_sintactico import Parser
from analizador_semantico import *
from codigo_intermedio import *
from mcl_tokens import *
from simbolos import TablaSimbolos
from gui import create_interface

# Variables globales
ultimo_ast = None
ultimo_tabla_simbolos = None
ultimo_codigo_intermedio = None

def analizar_codigo(editor, tabla, status_label, symbols_text):
    global ultimo_ast, ultimo_tabla_simbolos, ultimo_codigo_intermedio
    txt = editor.get("1.0", tk.END)
    tokens = AFD_Lexico(txt).run()
    tabla.delete(*tabla.get_children())
    for tag in editor.tag_names():
        editor.tag_remove(tag, "1.0", tk.END)
    editor.tag_delete("ERROR")

    for tok in tokens:
        tabla.insert("", tk.END, values=tok.to_tuple())
        s = f"1.0 + {tok.inicio} chars"
        e = f"1.0 + {tok.fin} chars"
        editor.tag_add(tok.tipo.name, s, e)

    status_label.config(text="", fg="green")
    try:
        tabla_simbolos = TablaSimbolos()
        parser = Parser(tokens, tabla_simbolos)
        ast = parser.program()
        ultimo_ast = ast
        ultimo_tabla_simbolos = tabla_simbolos

        # Análisis semántico
        semantico = AnalizadorSemantico(ast, tabla_simbolos)
        errores_semanticos = semantico.analizar()

        if parser.errors or errores_semanticos:
            errores = parser.errors + errores_semanticos
            status_label.config(text="\n".join(errores), fg="#FF5252")
        else:
            code_gen = CodeGenerator(tabla_simbolos)
            ultimo_codigo_intermedio = code_gen.generate(ast)
            status_label.config(text="✓ Análisis completado correctamente", fg="#4CAF50")

        # Actualizar tabla de símbolos
        actualizar_tabla_simbolos(symbols_text, tabla_simbolos)

    except SyntaxError as ex:
        msg = str(ex)
        status_label.config(text=msg, fg="red")
        m = re.search(r'\[pos (\d+)\]', msg)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < len(tokens):
                t = tokens[idx]
                s = f"1.0 + {t.inicio} chars"
                e = f"1.0 + {t.fin} chars"
                editor.tag_config("ERROR", background="yellow")
                editor.tag_add("ERROR", s, e)
    except Exception as ex:
        status_label.config(text=f"Error: {ex}", fg="red")

def actualizar_tabla_simbolos(symbols_text, tabla_simbolos):
    symbols_info = "📋 TABLA DE SÍMBOLOS\n\n"
    for i, tabla in enumerate(tabla_simbolos.tablas):
        symbols_info += f"🔹 Ámbito {i + 1}:\n"
        if not tabla:
            symbols_info += "   (vacío)\n"
        else:
            for nombre, simbolo in tabla.items():
                symbols_info += f"   • {nombre}: {simbolo.tipo}"
                if hasattr(simbolo, 'info') and simbolo.info:
                    info_str = ", ".join([f"{k}={v}" for k, v in simbolo.info.items()])
                    symbols_info += f" ({info_str})"
                symbols_info += "\n"
        symbols_info += "\n"

    symbols_text.config(state=tk.NORMAL)
    symbols_text.delete(1.0, tk.END)
    symbols_text.insert(tk.END, symbols_info)
    symbols_text.config(state=tk.DISABLED)

def ast_to_bnf(ast, nivel=0):
    def indent(n): return "  " * n
    if isinstance(ast, tuple):
        head, *rest = ast
        if not rest:
            return indent(nivel) + head
        lines = [indent(nivel) + head]
        for elem in rest:
            lines.append(ast_to_bnf(elem, nivel + 1))
        return "\n".join(lines)
    elif isinstance(ast, list):
        lines = []
        for item in ast:
            lines.append(ast_to_bnf(item, nivel))
        return "\n".join(lines)
    else:
        return indent(nivel) + repr(ast)

def mostrar_ast_manual(status_label):
    if ultimo_ast:
        ventana = tk.Toplevel()
        ventana.title("Árbol Sintáctico (Formato BNF)")
        ventana.geometry("600x600")
        txt = scrolledtext.ScrolledText(ventana, font=("Courier", 10))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, ast_to_bnf(ultimo_ast))
        txt.config(state=tk.DISABLED)
    else:
        status_label.config(text="⚠ AST no generado aún", fg="orange")

def mostrar_codigo_intermedio(status_label):
    if ultimo_codigo_intermedio:
        ventana = tk.Toplevel()
        ventana.title("Código Intermedio")
        ventana.geometry("800x600")
        notebook = ttk.Notebook(ventana)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Polish Notation
        polish_frame = ttk.Frame(notebook)
        notebook.add(polish_frame, text="Notación Polaca")
        polish_txt = scrolledtext.ScrolledText(polish_frame, font=("Courier", 10))
        polish_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        polish_txt.insert(tk.END, "\n".join(ultimo_codigo_intermedio["polish"]))
        polish_txt.config(state=tk.DISABLED)

        # P-Code
        pcode_frame = ttk.Frame(notebook)
        notebook.add(pcode_frame, text="Código P")
        pcode_txt = scrolledtext.ScrolledText(pcode_frame, font=("Courier", 10))
        pcode_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        pcode_txt.insert(tk.END, "\n".join(ultimo_codigo_intermedio["pcode"]))
        pcode_txt.config(state=tk.DISABLED)

        # Triples
        triples_frame = ttk.Frame(notebook)
        notebook.add(triples_frame, text="Triplos")
        triples_txt = scrolledtext.ScrolledText(triples_frame, font=("Courier", 10))
        triples_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        triples_txt.insert(tk.END, "\n".join(f"{i}: ({op}, {arg1 or '-'}, {arg2 or '-'})"
                                             for i, op, arg1, arg2 in ultimo_codigo_intermedio["triples"]))
        triples_txt.config(state=tk.DISABLED)

        # Quadruples
        quads_frame = ttk.Frame(notebook)
        notebook.add(quads_frame, text="Cuádruplos")
        quads_txt = scrolledtext.ScrolledText(quads_frame, font=("Courier", 10))
        quads_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        quads_txt.insert(tk.END, "\n".join(f"{i}: ({op}, {arg1 or '-'}, {arg2 or '-'}, {res or '-'})"
                                           for i, op, arg1, arg2, res in ultimo_codigo_intermedio["quads"]))
        quads_txt.config(state=tk.DISABLED)
    else:
        status_label.config(text="⚠ Código intermedio no generado aún", fg="orange")

def main():
    ui = create_interface()

    # Configurar eventos
    ui.editor.bind("<KeyRelease>", lambda e: analizar_codigo(ui.editor, ui.tabla, ui.status_label, ui.symbols_text))
    ui.btn_ast.config(command=lambda: mostrar_ast_manual(ui.status_label))
    ui.btn_code.config(command=lambda: mostrar_codigo_intermedio(ui.status_label))

    ui.root.mainloop()

if __name__ == "__main__":
    main()