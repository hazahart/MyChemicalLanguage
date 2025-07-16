import tkinter as tk
from tkinter import ttk, scrolledtext
import tkinter.font as tkFont
from dataclasses import dataclass
import platform
import subprocess
import os
from darkdetect import isDark

def is_dark_mode():
    return isDark()


# Paleta Material Design con ajustes para modo claro/oscuro
def get_theme_colors():
    dark_mode = is_dark_mode()

    if dark_mode:
        return {
            'primary': '#1F2937',
            'secondary': '#374151',
            'accent': '#3B82F6',
            'success': '#10B981',
            'warning': '#F59E0B',
            'danger': '#EF4444',
            'light': '#F9FAFB',
            'dark': '#111827',
            'bg_main': '#0F172A',
            'bg_secondary': '#1E293B',
            'text_primary': '#FFFFFF',
            'text_secondary': '#9CA3AF',
            'editor_bg': "#282C34",
            'editor_text': '#ABB2BF'
        }
    else:
        return {
            'primary': '#E5E7EB',
            'secondary': '#D1D5DB',
            'accent': '#2563EB',
            'success': '#059669',
            'warning': '#D97706',
            'danger': '#DC2626',
            'light': '#F3F4F6',
            'dark': '#1F2937',
            'bg_main': '#F9FAFB',
            'bg_secondary': '#FFFFFF',
            'text_primary': '#111827',
            'text_secondary': '#4B5563',
            'editor_bg': "#FFFFFF",
            'editor_text': '#1F2937'
        }

@dataclass
class UIComponents:
    root: tk.Tk
    editor: scrolledtext.ScrolledText
    tabla: ttk.Treeview
    status_label: tk.Label
    btn_ast: tk.Button
    btn_code: tk.Button
    symbols_tree: ttk.Treeview  # Cambiamos symbols_text por symbols_tree

class ModernFrame(tk.Frame):
    def __init__(self, parent, bg_color=None, **kwargs):
        colors = get_theme_colors()
        super().__init__(parent, bg=bg_color or colors['bg_secondary'], **kwargs)
        self.configure(relief='flat', bd=0)

class ModernButton(tk.Button):
    def __init__(self, parent, **kwargs):
        colors = get_theme_colors()
        super().__init__(parent, **kwargs)
        self.configure(
            bg=colors['accent'],
            fg=colors['text_primary'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            activebackground='#2563EB' if colors['accent'] == '#3B82F6' else '#1D4ED8',
            highlightthickness=2,
            highlightbackground=colors['accent'],
            highlightcolor=colors['accent']
        )
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_enter(self, e):
        colors = get_theme_colors()
        self.configure(bg='#2563EB' if colors['accent'] == '#3B82F6' else '#1D4ED8')

    def _on_leave(self, e):
        colors = get_theme_colors()
        self.configure(bg=colors['accent'])

class ModernLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        colors = get_theme_colors()
        super().__init__(parent, **kwargs)
        self.configure(
            bg=kwargs.get('bg', colors['bg_secondary']),
            fg=colors['text_primary'],
            font=('Segoe UI', 10)
        )

def create_interface():
    dark_mode = is_dark_mode()
    THEME_COLORS = get_theme_colors()

    syntax_colors = {
        "dark": {  # One Dark
                 "PALABRA_RESERVADA": ("#C678DD", "bold"),
                 "UNIDAD": ("#56B6C2", "normal"),
                 "IDENTIFICADOR": ("#ABB2BF", "italic"),
                 "NUMERO": ("#D19A66", "normal"),
                 "OPERADOR": ("#61AFEF", "normal"),
                 "PUNTUACION": ("#E06C75", "normal"),
                 "LLAVE": ("#E5C07B", "normal"),
                 "PAR_CORCHETE": ("#E5C07B", "normal"),
                 "TEXTO": ("#98C379", "normal"),
                 "COMENTARIO": ("#5C6370", "italic"),
                 "DESCONOCIDO": ("#FF5555", "bold"),
                 "bg": "#282C34",
                 "fg": "#ABB2BF",
                 "FUSIONAR": ("#61AFEF", "bold"),
                 "SEPARAR": ("#61AFEF", "bold"),
                 "CATALIZAR": ("#61AFEF", "bold"),
                 "DILUIR": ("#61AFEF", "bold"),
                 },
        "light": {  # Xcode
                  "PALABRA_RESERVADA": ("#0000FF", "bold"),
                  "UNIDAD": ("#C41A16", "normal"),
                  "IDENTIFICADOR": ("#234A97", "italic"),
                  "NUMERO": ("#1C00CF", "normal"),
                  "OPERADOR": ("#000000", "normal"),
                  "PUNTUACION": ("#000000", "normal"),
                  "LLAVE": ("#8B4513", "normal"),
                  "PAR_CORCHETE": ("#8B4513", "normal"),
                  "TEXTO": ("#008000", "normal"),
                  "COMENTARIO": ("#808080", "italic"),
                  "DESCONOCIDO": ("#FF0000", "bold"),
                  "bg": "#FFFFFF",
                  "fg": "#000000",
                  "FUSIONAR": ("#000000", "bold"),
                  "SEPARAR": ("#000000", "bold"),
                  "CATALIZAR": ("#000000", "bold"),
                  "DILUIR": ("#000000", "bold"),
                  }
    }

    theme = syntax_colors["dark"] if dark_mode else syntax_colors["light"]
    THEME_COLORS['editor_bg'] = theme["bg"]
    THEME_COLORS['editor_text'] = theme["fg"]

    root = tk.Tk()
    root.title("Analizador de My Chemical Language (MCL)")
    root.configure(bg=THEME_COLORS['bg_main'])

    title_font = tkFont.Font(family='Segoe UI', size=16, weight='bold')
    header_font = tkFont.Font(family='Segoe UI', size=12, weight='bold')
    code_font = tkFont.Font(family='Consolas', size=11)

    main_frame = ModernFrame(root, bg_color=THEME_COLORS['bg_main'])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    header_frame = ModernFrame(main_frame, bg_color=THEME_COLORS['primary'])
    header_frame.pack(fill=tk.X, pady=(0, 20))

    title_label = tk.Label(header_frame,
                           text="🧪 Analizador de My Chemical Language (MCL)",
                           font=title_font,
                           bg=THEME_COLORS['primary'],
                           fg=THEME_COLORS['text_primary'])
    title_label.pack(pady=15)

    content_frame = ModernFrame(main_frame)
    content_frame.pack(fill=tk.BOTH, expand=True)

    left_panel = ModernFrame(content_frame, bg_color=THEME_COLORS['bg_secondary'])
    left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    editor_header = ModernFrame(left_panel, bg_color=THEME_COLORS['secondary'])
    editor_header.pack(fill=tk.X, pady=(0, 10))

    editor_title = ModernLabel(editor_header,
                               text="📝 Editor de Código MCL",
                               font=header_font,
                               bg=THEME_COLORS['secondary'])
    editor_title.pack(side=tk.LEFT, padx=15, pady=10)

    btn_frame = ModernFrame(editor_header, bg_color=THEME_COLORS['secondary'])
    btn_frame.pack(side=tk.RIGHT, padx=15, pady=5)

    btn_ast = ModernButton(btn_frame, text="🌳 Ver AST")
    btn_ast.pack(side=tk.LEFT, padx=5)

    btn_code = ModernButton(btn_frame, text="📜 Código Intermedio")
    btn_code.pack(side=tk.LEFT, padx=5)

    editor_frame = ModernFrame(left_panel, bg_color=THEME_COLORS['editor_bg'])
    editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    editor = scrolledtext.ScrolledText(editor_frame,
                                       font=code_font,
                                       bg=THEME_COLORS['editor_bg'],
                                       fg=THEME_COLORS['editor_text'],
                                       insertbackground=THEME_COLORS['editor_text'],
                                       selectbackground=THEME_COLORS['accent'],
                                       selectforeground=THEME_COLORS['text_primary'],
                                       wrap=tk.NONE,
                                       relief='flat',
                                       bd=0,
                                       padx=15,
                                       pady=15)
    editor.pack(fill=tk.BOTH, expand=True)

    # Panel derecho con notebook
    right_panel = ModernFrame(content_frame, bg_color=THEME_COLORS['bg_secondary'])
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

    notebook = ttk.Notebook(right_panel)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TNotebook', background=THEME_COLORS['bg_secondary'])
    style.configure('TNotebook.Tab',
                    background=THEME_COLORS['secondary'],
                    foreground=THEME_COLORS['text_primary'],
                    padding=[16, 8],
                    font=('Segoe UI', 10, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', THEME_COLORS['accent'])])

    tokens_frame = ModernFrame(notebook, bg_color=THEME_COLORS['bg_secondary'])
    notebook.add(tokens_frame, text="🔍 Tokens")

    tabla_frame = ModernFrame(tokens_frame)
    tabla_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    cols = ("Tipo", "Valor", "Código")
    tabla = ttk.Treeview(tabla_frame, columns=cols, show="headings", height=15)

    style.configure('Treeview',
                    background=THEME_COLORS['light'],
                    foreground=THEME_COLORS['dark'],
                    fieldbackground=THEME_COLORS['light'],
                    font=('Segoe UI', 9),
                    rowheight=28)
    style.map('Treeview', background=[('selected', '#DBEAFE')])
    style.configure('Treeview.Heading',
                    background=THEME_COLORS['accent'],
                    foreground=THEME_COLORS['text_primary'],
                    font=('Segoe UI', 10, 'bold'),
                    relief='flat')

    for c in cols:
        tabla.heading(c, text=c)
        tabla.column(c, width=120, anchor="center")

    scrollbar = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scrollbar.set)
    tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    symbols_frame = ModernFrame(notebook, bg_color=THEME_COLORS['bg_secondary'])
    notebook.add(symbols_frame, text="📊 Símbolos")

    symbols_tree = ttk.Treeview(symbols_frame, columns=("Nombre", "Tipo", "Info"), show="headings", height=15)
    symbols_tree.heading("Nombre", text="Nombre")
    symbols_tree.heading("Tipo", text="Tipo")
    symbols_tree.heading("Info", text="Información adicional")
    symbols_tree.column("Nombre", width=150, anchor="w")
    symbols_tree.column("Tipo", width=100, anchor="w")
    symbols_tree.column("Info", width=250, anchor="w")

    scrollbar = ttk.Scrollbar(symbols_frame, orient=tk.VERTICAL, command=symbols_tree.yview)
    symbols_tree.configure(yscrollcommand=scrollbar.set)
    symbols_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    status_frame = ModernFrame(main_frame, bg_color=THEME_COLORS['secondary'])
    status_frame.pack(fill=tk.X, pady=(20, 0))

    status_label = tk.Label(status_frame,
                            text="💡 Listo para analizar código MCL",
                            font=('Segoe UI', 10),
                            bg=THEME_COLORS['secondary'],
                            fg=THEME_COLORS['text_primary'],
                            anchor="w")
    status_label.pack(fill=tk.X, padx=20, pady=15)

    for tag in theme:
        if tag in ("bg", "fg"):
            continue
        fg, st = theme[tag]
        ft = (code_font.cget("family"), code_font.cget("size"), st) if st != "normal" else code_font
        editor.tag_config(tag, foreground=fg, font=ft)

    W, H = 1200, 800
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

    return UIComponents(
        root=root,
        editor=editor,
        tabla=tabla,
        status_label=status_label,
        btn_ast=btn_ast,
        btn_code=btn_code,
        symbols_tree=symbols_tree
    )

# Ejecutar la interfaz
if __name__ == "__main__":
    ui = create_interface()
    ui.root.mainloop()