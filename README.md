# MyChemicalLanguage (MCL) - Lenguaje de Simulación Química

**MyChemicalLanguage (MCL)** es un lenguaje de programación especializado diseñado para modelar y simular reacciones químicas. Este proyecto incluye un compilador completo con análisis léxico, sintáctico, semántico y generación de código intermedio, junto con una interfaz gráfica intuitiva.

## Características Principales

- **Sintaxis Química Especializada**: Declara sustancias, cantidades, unidades y reacciones químicas
- **Operadores Verbales**: `fusionar`(+), `separar`(-), `catalizar`(*), `diluir`(/)
- **Constantes Científicas**: `PLANCK`, `AVOGADRO`, `PI` integradas
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
  - Detección automática de modo oscuro/claro

## Componentes del Proyecto

| Archivo                    | Descripción                                   |
|----------------------------|-----------------------------------------------|
| `analizador_lexico.py`     | Implementa AFD y Trie para tokenización       |
| `analizador_sintactico.py` | Parser para construcción de AST               |
| `analizador_semantico.py`  | Verificador de tipos y consistencia química   |
| `codigo_intermedio.py`     | Genera representaciones intermedias de código |
| `gui.py`                   | Interfaz gráfica con Tkinter y modo oscuro    |
| `main.py`                  | Punto de entrada principal                    |
| `mcl_tokens.py`            | Definición de tokens y enumeraciones          |
| `simbolos.py`              | Implementación de tabla de símbolos           |

## Ejemplo de Código MCL

```mcl
# Declaración de las sustancias iniciales
sustancia H2 cantidad = 2.0 mol @[25 gradC, 1 atm];
sustancia O2 cantidad = 1.0 mol @[32 gradC, 1 atm];

# Mezcla de H2 y O2 para crear agua
mezclar (H2 fusionar O2) -> agua;

# Mostrar propiedades de la sustancia resultante
mostrar("Temperatura de agua: ", agua.temp, " °C");
mostrar("Presión de agua: ", agua.presion, " atm");

# Declaración adicional de otra sustancia para probar compatibilidad
sustancia N2 cantidad = 1.5 mol @[30 gradC, 1 atm];

# Mezcla adicional con N2
mezclar (agua fusionar N2) -> mezcla;

# Mostrar resultado de la nueva mezcla
mostrar("Temperatura de mezcla: ", mezcla.temp, " °C");
mostrar("Presión de mezcla: ", mezcla.presion, " atm");

# Añadir una operación simple para verificar cantidad
mostrar("Cantidad total de mezcla: ", mezcla.cant, " mol");
```