class PeepholeOptimizer:
    def __init__(self, pcode):
        self.pcode = pcode

    def optimizar(self):
        print("[PeepholeOptimizer] Ejecutando optimización de mirilla sobre P-code...")
        nueva = []
        i = 0
        while i < len(self.pcode):
            actual = self.pcode[i]
            siguiente = self.pcode[i+1] if i+1 < len(self.pcode) else None

            # Eliminación de instrucciones duplicadas
            if siguiente and actual == siguiente:
                i += 1
                continue

            # Patrones simples: LIT 0 / ADD -> eliminar si no útil
            if i+1 < len(self.pcode):
                if ("LIT 0" in self.pcode[i] and "ADD" in self.pcode[i+1]):
                    i += 2
                    continue

            nueva.append(actual)
            i += 1

        return nueva