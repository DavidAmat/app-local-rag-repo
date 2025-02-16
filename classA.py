from classB import ClassB, ClassB2

class ClassA:
    def __init__(self):
        print("ClassA.__init__()")
        self.a = 1
        self.classA2 = ClassA2()
        self.classB = ClassB()

    def method1(self, a: int) -> int:
        classA2 = ClassA2()
        b = classA2.method1(a)
        b2 = ClassB2.method3(b)
        return b2
    
    def method2(self, a: int) -> int:
        b = self.classA2.method2(a)
        b2 = self.classB.method1(b)
        return b2
        

class ClassA2:
    def __init__(self):
        print("ClassA2.__init__()")
        self.a = 1

    def method1(self, a: int) -> int:
        return a + 1
    
    def method2(self, a: int) -> int:
        return a + 2
    
    def method3(self, a: int) -> int:
        return a + 3