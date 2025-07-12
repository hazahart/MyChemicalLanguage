# MyChemicalLanguage (MCL) - Lenguaje de Simulación Química

**MyChemicalLanguage (MCL)** es un lenguaje de programación especializado diseñado para modelar y simular reacciones químicas. Este proyecto incluye un compilador completo con análisis léxico, sintáctico, semántico y generación de código intermedio, junto con una interfaz gráfica intuitiva.

## Características Principales

- **Sintaxis Química Especializada**: Declara sustancias, cantidades, unidades y reacciones químicas
- **Análisis Multinivel**:
  - **Léxico**: Reconocimiento de tokens químicos (mol, atm, sustancias)
  - **Sintáctico**: Construcción de Abstract Syntax Tree (AST)
  - **Semántico**: Verificación de tipos, unidades y consistencia química
- **Generación de Código Intermedio**:
  - Notación polaca
  - Código P
  - Triplos y Cuádruplos
- **Interfaz Gráfica Moderna**:
  - Editor de código con resaltado sintáctico
  - Visualización de tokens
  - Tabla de símbolos interactiva
  - Visualización de AST y código intermedio

## Componentes del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `analizador_lexico.py` | Implementa AFD y Trie para tokenización |
| `analizador_sintactico.py` | Parser para construcción de AST |
| `analizador_semantico.py` | Verificador de tipos y consistencia química |
| `codigo_intermedio.py` | Genera representaciones intermedias de código |
| `gui.py` | Interfaz gráfica con Tkinter |
| `main.py` | Punto de entrada principal |
| `mcl_tokens.py` | Definición de tokens y enumeraciones |
| `simbolos.py` | Implementación de tabla de símbolos |

## Ejemplo de Código MCL

```mcl
# Simula la formación de agua y calcula la masa de reactivos
sustancia H2 cantidad=2.016 mol @[25 gradC, 1 atm];
sustancia O2 cantidad=32.00 mol @[25 gradC, 1 atm];
sustancia H2O cantidad=18.015 gramo;
sustancia reactivoH2 cantidad = 0;
sustancia reactivoO2 cantidad = 0;

sustancia total cantidad = 0;

reaccionar formarAgua[2H2, O2 -> 2H2O] {
    mezclar(H2 * 2) -> reactivoH2;
    mezclar(O2 * 1) -> reactivoO2;
    mezclar(reactivoH2 + reactivoO2) -> total;
    mostrar("Masa total de reactivos para formar agua: ", total, " gramo");
}

mostrar("¡Hola Mundo Químico! Iniciando reacción...");
formarAgua[2H2, O2];
```