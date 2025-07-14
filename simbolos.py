class Simbolo:
    def __init__(self, nombre, tipo, **kwargs):
        self.nombre = nombre
        self.tipo = tipo
        self.info = kwargs

class TablaSimbolos:
    def __init__(self):
        self.tablas = [{}]
        # Agregar constantes predefinidas
        self.insertar("PLANCK", Simbolo("PLANCK", "numero", valor=6.62607015e-34))
        self.insertar("AVOGADRO", Simbolo("AVOGADRO", "numero", valor=6.02214076e23))
        self.insertar("PI", Simbolo("PI", "numero", valor=3.1415926535))

    def entrar_bloque(self):
        self.tablas.append({})

    def salir_bloque(self):
        if len(self.tablas) > 1:
            self.tablas.pop()

    def insertar(self, nombre, simbolo):
        self.tablas[-1][nombre] = simbolo

    def buscar(self, nombre):
        for tabla in reversed(self.tablas):
            if nombre in tabla:
                return tabla[nombre]
        return None

    def existe_en_actual(self, nombre):
        return nombre in self.tablas[-1]