import ast
import os
from typing import Dict, List, Optional, Set
from pathlib import Path
from typing import List, Optional, Set

class Node:
    def __init__(self, name: str, path: str, parent: Optional['Node'] = None):
        self.name = name.strip()
        self.path = path.strip()  # Full relative path (e.g., "folder1/folder2/script.py")
        self.parent = parent      # Parent node in the hierarchy
        self.children: List[Node] = []

    def add_child(self, node: 'Node'):
        if node not in self.children:
            self.children.append(node)
            node.parent = self  # Set parent when adding child

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, {self.path})"


class FolderNode(Node):
    def __init__(self, name: str, path: str, parent: Optional['Node'] = None):
        super().__init__(name, path, parent)

    def __setattr__(self, key, value):
        if isinstance(value, Node):
            self.__dict__[key] = value
        else:
            super().__setattr__(key, value)

    def add_child(self, node: 'Node'):
        super().add_child(node)
        # Dynamically add an attribute for easy access
        if isinstance(node, FolderNode) or isinstance(node, ScriptNode):
            setattr(self, node.name, node)


class ScriptNode(Node):
    def __init__(self, name: str, path: str, parent: Optional['Node'] = None):
        super().__init__(name, path, parent)
        # New fields for tracking dependencies/aliases
        self.script_dependencies: List['ScriptNode'] = []
        self.class_dependencies: List['ClassNode'] = []
        self.function_dependencies: List['FunctionNode'] = []
        # Map alias -> fully qualified node path (e.g. "CA" -> "folder/script1.py::classA")
        self.aliases: Dict[str, str] = {}

class FunctionNode(Node):
    def __init__(self, name: str, path: str, parent: Optional['Node'] = None):
        super().__init__(name, path, parent)

class ClassNode(Node):
    def __init__(self, name: str, path: str, parent: Optional['Node'] = None):
        super().__init__(name, path, parent)
        self.aliases: Set[str] = set()  # Aliases from imports (e.g., "ClassA" for "classAmpere")

class MethodNode(Node):
    def __init__(self, name: str, path: str, parent: Optional['Node'] = None, is_static: bool = False):
        super().__init__(name, path, parent)
        self.is_static = is_static
        self.dependencies: List[Node] = []  # Method call dependencies

    def add_dep(self, node: 'Node'):
        if node not in self.dependencies:
            self.dependencies.append(node)

# ------------------------------------------------- #
#             FOLDER SCRIPT BUILDER
# ------------------------------------------------- #
class FolderScriptBuilder:
    """Builds folder and script nodes from the filesystem, with global_path as root."""
    def __init__(self, global_path: str):
        self.global_path = global_path

    def build(self) -> Node:
        root = FolderNode("root", ".", None)  # Root node represents global_path
        # Set the root name to the last part of the global path
        global_path = Path(self.global_path)
        root.name = global_path.parts[-1]

        nodes: Dict[str, Node] = {"root": root}  # Path "" maps to root

        for root_dir, _, filenames in os.walk(self.global_path):
            rel_root = os.path.relpath(root_dir, self.global_path)
            parent = root

            if rel_root != ".":
                parts = rel_root.split("/")
                for i, part in enumerate(parts):
                    folder_path = "/".join(parts[:i + 1])
                    if folder_path not in nodes:
                        folder_node = FolderNode(part, folder_path)
                        nodes[folder_path] = folder_node
                        parent.add_child(folder_node)
                    parent = nodes[folder_path]

            for fname in filenames:
                if fname.endswith(".py"):
                    rel_path = os.path.join(rel_root, fname) if rel_root != "." else fname
                    script_node = ScriptNode(fname, rel_path)
                    nodes[rel_path] = script_node
                    parent.add_child(script_node)

        return root, nodes
    
# ------------------------------------------------- #
#             SCRIPT ANALYZER
# ------------------------------------------------- #
class ScriptAnalyzer:
    def __init__(self, nodes: Dict[str, Node], global_path: str, query_folder: Optional[str] = None):
        self.nodes = nodes
        self.global_path = Path(global_path)
        self.query_folder = self.global_path / query_folder if query_folder else self.global_path
        self.ast_cache = {}
        self._build_ast()

    def _build_ast(self):
        for path, node in list(self.nodes.items()):
            if isinstance(node, ScriptNode):
                full_path = self.global_path / node.path
                if full_path.exists() and full_path.is_relative_to(self.query_folder):
                    with open(full_path, "r") as file:
                        self.ast_cache[path] = ast.parse(file.read())

    def analyze(self):
        script_nodes = list(self.nodes.items())
        for path, node in script_nodes:
            if isinstance(node, ScriptNode) and path in self.ast_cache:
                tree = self.ast_cache[path]
                self._process_script(node, tree)

    def _process_script(self, script_node: ScriptNode, tree: ast.Module):
        for ast_node in tree.body:
            if isinstance(ast_node, ast.ClassDef):
                self._process_class(script_node, ast_node)
            elif isinstance(ast_node, ast.FunctionDef):
                self._process_function(script_node, ast_node)

    def _process_class(self, script_node: ScriptNode, ast_node: ast.ClassDef):
        class_path = f"{script_node.path}::{ast_node.name}"
        class_node = ClassNode(ast_node.name, class_path, script_node)
        self.nodes[class_path] = class_node
        script_node.add_child(class_node)

        for method in ast_node.body:
            if isinstance(method, ast.FunctionDef):
                method_path = f"{class_path}::{method.name}"
                method_node = MethodNode(method.name, method_path, class_node)
                self.nodes[method_path] = method_node
                class_node.add_child(method_node)

    def _process_function(self, script_node: ScriptNode, ast_node: ast.FunctionDef):
        function_path = f"{script_node.path}::{ast_node.name}"
        function_node = FunctionNode(ast_node.name, function_path, script_node)
        self.nodes[function_path] = function_node
        script_node.add_child(function_node)

# ------------------------------------------------- #
#             IMPORT ANALYZER
# ------------------------------------------------- #
class ImportAnalyzer:
    def __init__(self, global_path: str, nodes: Dict[str, Node], ast_cache: Dict[str, ast.Module], query_folder: Optional[str] = None):
        self.global_path = Path(global_path)
        self.nodes = nodes
        self.ast_cache = ast_cache
        self.query_folder = self.global_path / query_folder if query_folder else self.global_path

    def analyze(self, script_path: Optional[str] = None):
        if script_path:
            script_node = self.nodes.get(script_path)
            if isinstance(script_node, ScriptNode) and script_path in self.ast_cache:
                tree = self.ast_cache[script_path]
                self._process_imports(script_node, tree)
        else:
            for path, node in self.nodes.items():
                full_path = self.global_path / path
                if isinstance(node, ScriptNode) and path in self.ast_cache and full_path.is_relative_to(self.query_folder):
                    tree = self.ast_cache[path]
                    self._process_imports(node, tree)


    def _process_imports(self, script_node: ScriptNode, tree: ast.Module):
        for stmt in tree.body:
            if isinstance(stmt, ast.Import):
                self._handle_import(script_node, stmt)
            elif isinstance(stmt, ast.ImportFrom):
                self._handle_import_from(script_node, stmt)

    def _handle_import(self, script_node: ScriptNode, stmt: ast.Import):
        """
        Example:
            import script2
            import script2 as s2
            import script1, script2 as s2
        """
        for alias in stmt.names:
            module_name = alias.name
            as_name = alias.asname or module_name

            script_path = self._find_script_path(module_name, base_path=script_node.path)
            if script_path and script_path in self.nodes and isinstance(self.nodes[script_path], ScriptNode):
                target_node: ScriptNode = self.nodes[script_path]
                
                # Ensure no duplicate dependencies using a set for paths
                if target_node not in set(script_node.script_dependencies):
                    script_node.script_dependencies.append(target_node)
                    script_node.aliases[as_name] = script_path

    def _handle_import_from(self, script_node: ScriptNode, stmt: ast.ImportFrom):
        """
        Example:
            from script1 import classA, functionB as fB
            from . import something
            from .script2 import SomeClass
        """
        module_name = stmt.module or ""
        level = stmt.level
        from_script_path = self._find_script_path(module_name, level, script_node.path)

        if not from_script_path or from_script_path not in self.nodes:
            return

        from_script_node = self.nodes[from_script_path]
        if not isinstance(from_script_node, ScriptNode):
            return

        for alias in stmt.names:
            imported_name = alias.name
            as_name = alias.asname or imported_name

            fq_path = f"{from_script_path}::{imported_name}"
            if fq_path in self.nodes:
                # If it's a ClassNode
                if isinstance(self.nodes[fq_path], ClassNode):
                    class_node = self.nodes[fq_path]
                    script_node.class_dependencies.append(class_node)
                    script_node.aliases[as_name] = fq_path
                # If it's a FunctionNode
                elif isinstance(self.nodes[fq_path], FunctionNode):
                    func_node = self.nodes[fq_path]
                    script_node.function_dependencies.append(func_node)
                    script_node.aliases[as_name] = fq_path
            else:
                # If no symbol match is found, treat as entire script import
                if from_script_node not in set(script_node.script_dependencies):
                    script_node.script_dependencies.append(from_script_node)
                    # script_node.aliases[as_name] = from_script_path

    def _find_script_path(self, module_name: str, level: int = 0, base_path: str = "") -> Optional[str]:
        if not module_name and level == 0:
            return None

        # Convert module name using dot notation to a relative script path
        relative_path = Path(module_name.replace(".", "/")).with_suffix(".py")
        
        # If relative path exists in nodes, return it
        return str(relative_path) if str(relative_path) in self.nodes else None
    

# ------------------------------------------------- #
#             CODE PARSER
# ------------------------------------------------- #
import ast
import os
from typing import Dict, List, Set

def get_dependencies(filepath: str) -> Dict[str, Set[str]]:
    dependencies: Dict[str, Set[str]] = {}
    with open(filepath, "r") as f:
        tree = ast.parse(f.read())

    imports = {}  # Store imported modules and their aliases
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module_path = node.module
            for alias in node.names:
                imported_name = alias.name if alias.asname is None else alias.asname
                imports[imported_name] = module_path + "." + alias.name #corrected: add alias.name

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            dependencies[func_name] = set()
            local_vars = {}

            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Assign):
                    for target in subnode.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            if isinstance(subnode.value, ast.Call):
                                if isinstance(subnode.value.func, ast.Name):
                                    called_class = subnode.value.func.id
                                    if called_class in imports:
                                        full_class_path = imports[called_class]
                                        local_vars[var_name] = full_class_path
                                elif isinstance(subnode.value.func, ast.Attribute):
                                    module_name = subnode.value.func.value.id
                                    called_class = subnode.value.func.attr
                                    if module_name in imports:
                                        full_class_path = imports[module_name] + "." + called_class
                                        local_vars[var_name] = full_class_path

                elif isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Attribute):
                        try:
                            obj_name = subnode.func.value.id
                            method_name = subnode.func.attr
                            if obj_name in local_vars:
                                obj_type = local_vars[obj_name]
                                dependencies[func_name].add(f"{obj_type}.{method_name}")
                            elif isinstance(subnode.func.value, ast.Name): # If the value is not a local variable it is a module
                                if subnode.func.value.id in imports:
                                    dependencies[func_name].add(f"{imports[subnode.func.value.id]}.{method_name}") # If the value is not a local variable it is a module
                                else:
                                    dependencies[func_name].add(f"{subnode.func.value.id}.{method_name}") # If the value is not a local variable it is a module

                            elif isinstance(subnode.func.value, ast.Attribute): # If the value is another attribute
                                module_name = subnode.func.value.value.id
                                method_name = f"{subnode.func.value.attr}.{subnode.func.attr}"
                                if module_name in imports:
                                    dependencies[func_name].add(f"{imports[module_name]}.{method_name}")
                                else:
                                    dependencies[func_name].add(f"{module_name}.{method_name}")
                        except AttributeError:
                           pass

                    elif isinstance(subnode.func, ast.Name):
                        called_function = subnode.func.id
                        if called_function in imports:
                            dependencies[func_name].add(imports[called_function])
                        else:
                            dependencies[func_name].add(called_function)

    return dependencies


def simplify_dependencies(dependencies: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    simplified_deps = {}
    for caller, callees in dependencies.items():
        simplified_deps[caller] = set()
        for callee in callees:
            parts = callee.split(".")
            if len(parts) > 1:
                simplified_deps[caller].add(".".join(parts))  # Keep only module/class.method
            else:
                simplified_deps[caller].add(callee) # If it is a function call, keep it as is
    return simplified_deps


if __name__ == "__main__":
    global_path = "/home/david/Documents/glovo/machine-learning-platform/"
    script_path = "widget_framework/api.py"
    query_folder = "widget_framework"
    filepath = os.path.join(global_path, script_path)

    # 0) Build the folder and script nodes
    fsb = FolderScriptBuilder(global_path)
    root, nodes = fsb.build()

    # 1) Build Script/Class/Function/Method nodes
    script_analyzer = ScriptAnalyzer(
        nodes=nodes, 
        global_path=global_path,
        query_folder=query_folder
    )
    script_analyzer.analyze()

    # 2) Build the import relationships
    import_analyzer = ImportAnalyzer(
        global_path=global_path, 
        nodes=nodes, 
        ast_cache=script_analyzer.ast_cache,
        query_folder=query_folder
    )
    import_analyzer.analyze("widget_framework/api.py")

    # RESULTS so far:
    #     vars(nodes["widget_framework/api.py"])["class_dependencies"]
    #     [ClassNode(ContractInput, widget_framework/src/utils.py::ContractInput),
    #  ClassNode(Utils, widget_framework/src/utils.py::Utils),
    #  ClassNode(WidgetBuilder, widget_framework/src/widget_builder.py::WidgetBuilder)]


    # Get the dependencies of each function / method to the classes and functions they call
    # which are defined either in the same script or imported in the imports
        
    deps = get_dependencies(filepath)
    simplified_deps = simplify_dependencies(deps)

    for caller, callees in simplified_deps.items():
        print(f"{caller}:")
        for callee in callees:
            print(f"  - {callee}")

    # inference:
    # - tracer.trace
    # - widget_framework.src.widget_builder.WidgetBuilder
    # - widget_framework.src.widget_builder.WidgetBuilder.run
    # production_app:
    # - widget_framework.src.utils.Utils.read_avro_contract
    # - inference
    # - py_kit.core.tracing.get_tracer
    # - glovo_mlp_coreutils.training_logger.get_training_logger
    # - glovo_mlp_core.api.api.api
    # - glovo_mlp_coreutils.metrics.Metrics.statsd_from_env
    # local_app:
    # - widget_framework.src.utils.Utils.read_avro_contract
    # - inference
    # - py_kit.core.tracing.get_tracer
    # - glovo_mlp_coreutils.training_logger.get_training_logger
    # - glovo_mlp_core.api.api.api
    # - glovo_mlp_coreutils.metrics.Metrics.statsd_from_env