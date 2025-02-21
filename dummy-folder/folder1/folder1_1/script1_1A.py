from script1 import classA as CA
import script2
from folder1.folder1_1.script1_1B import indep_fun_11B

class Class11AA:
    def __init__(self):
        self.a = 1
        self.classA = CA()

    def method1(self, a: int) -> int:
        a1 = self.classA.method1(a)
        c = indep_fun_11B(a1)
        b2 = script2.classB().method3(a1+c)
        return b2
    
    def method2(self, a: int) -> int:
        return a
        

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