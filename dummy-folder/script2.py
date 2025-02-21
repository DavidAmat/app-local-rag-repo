class ClassB:
    def __init__(self):
        self.a = 1
        self.ClassB2 = ClassB2()

    def method1(self, a: int) -> int:
        b = self.ClassB2.method1(a)
        return b
    
    def method2(self, a: int) -> int:
        b = self.ClassB2.method2(a)
        return b
    
class ClassB2:
    def __init__(self):
        self.a = 1

    def method1(self, a: int) -> int:
        return a * 1
    
    def method2(self, a: int) -> int:
        return a * 2
    
    @staticmethod
    def method3(a: int) -> int:
        return a * 3