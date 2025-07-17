class PeepholeOptimizer:
    def __init__(self, pcode):
        self.pcode = pcode
        self.removed = []  # Lista para guardar instrucciones eliminadas

    def optimizar(self):
        nueva = []
        i = 0
        while i < len(self.pcode):
            actual = self.pcode[i]
            siguiente = self.pcode[i+1] if i+1 < len(self.pcode) else None

            # Eliminación de instrucciones duplicadas
            if siguiente and actual == siguiente:
                self.removed.append(actual)  # Registrar eliminación
                i += 1
                continue

            # Patrones simples: LIT 0 / ADD -> eliminar si no útil
            if i+1 < len(self.pcode):
                if "LIT 0" in actual and "ADD" in self.pcode[i+1]:
                    self.removed.append(actual)          # Registrar primera eliminación
                    self.removed.append(self.pcode[i+1])  # Registrar segunda eliminación
                    i += 2
                    continue

            nueva.append(actual)
            i += 1
            
        return nueva, self.removed  # Devolver tanto el código optimizado como las eliminaciones