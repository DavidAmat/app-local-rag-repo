from folder1.folder1_1.script1_1A import Class11AA
from script1 import classA2

def indep_fun_11B(a: int) -> int:
    return a + 1

class Class11B:
    def __init__(self):
        self.a = 1
        self.class11AA = Class11AA()

    def method1(self, a: int) -> int:
        a1 = self.class11AA.method1(a)
        b = classA2.method1(a1)
        return b
    
    def method2(self, a: int) -> int:
        b = self.classA2.method2(a)
        b2 = self.classB.method1(b)
        return b2