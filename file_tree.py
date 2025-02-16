import os

class FileTreeGraph:
    """
    This class builds a DAG representing the file tree of a given directory.
    Each folder is a node and each file is a leaf node.
    The graph is maintained as two lists: 'nodes' and 'edges'.
    """
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.nodes = []
        self.edges = []
        self.node_id = 0  # Unique id for each node

    def add_node(self, label, node_type, parent_id=None):
        """
        Add a node to the graph. 'node_type' can be 'folder' or 'file'.
        If parent_id is provided, create an edge from the parent to the new node.
        """
        current_id = self.node_id
        self.nodes.append({
            "id": current_id,
            "label": label,
            "type": node_type
        })
        if parent_id is not None:
            self.edges.append({
                "from": parent_id,
                "to": current_id
            })
        self.node_id += 1
        return current_id

    def build_graph(self, current_path=None, parent_id=None):
        """
        Recursively traverse the directory tree starting from 'current_path'.
        For each folder or file, add a node (and an edge if it has a parent).
        """
        if current_path is None:
            current_path = self.root_path

        # For the very first call, create a node for the root folder.
        if parent_id is None:
            current_id = self.add_node(os.path.basename(current_path) or current_path, "folder")
        else:
            current_id = parent_id

        try:
            for entry in os.listdir(current_path):
                full_path = os.path.join(current_path, entry)
                if os.path.isdir(full_path):
                    # Create a node for the folder, then recursively build its subgraph.
                    folder_id = self.add_node(entry, "folder", current_id)
                    self.build_graph(full_path, folder_id)
                else:
                    # Create a node for the file.
                    self.add_node(entry, "file", current_id)
        except Exception as e:
            print(f"Error reading directory {current_path}: {e}")

    def get_graph(self):
        """
        Return the graph as a dictionary with two keys: 'nodes' and 'edges'.
        This format is easy to convert to JSON for web visualization.
        """
        return {"nodes": self.nodes, "edges": self.edges}
    
if __name__ == "__main__":
    # Example usage
    file_tree = FileTreeGraph("/home/david/Documents/glovo/machine-learning-platform/widget-framework/")
    file_tree.build_graph()
    print(file_tree.get_graph())