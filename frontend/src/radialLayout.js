// radialLayout.js

/**
 * Recursively assigns radial positions to each node and returns flattened nodes/links.
 * - The root node has angleRange = 2π (360°).
 * - Nested nodes have a reduced angle range (e.g., ±45° around the parent's angle).
 * - Objects have a smaller radius increment than files.
 */
export function radialLayout(dagData) {
    const nodes = [];
    const links = [];
    let globalId = 0;
  
    // Configuration
    const distanceFile = 100;    // radial increment for .py files
    const distanceObject = 50;   // radial increment for imported objects
    const defaultSubAngle = (45 * Math.PI) / 180; // ±45° => 90° total
  
    /**
     * Recursively process a DAG node, assigning radial positions and building up nodes[]/links[].
     * @param {*} nodeData - The current DAG node (e.g., { name, imports, imported_objects }).
     * @param {number} parentAngle - The angle of the parent node in radians.
     * @param {number} angleRange - The allowable angle range for this node's children in radians.
     * @param {number} parentRadius - The radial distance of the parent node from the root.
     * @param {number} level - Depth of this node in the DAG (0 => root).
     * @param {number|null} parentId - The ID of the parent node for linking.
     */
    function assignPositions(
      nodeData,
      parentAngle,
      angleRange,
      parentRadius,
      level,
      parentId
    ) {
      // Determine if this node is the root (level=0).
      // Otherwise, check if nodeData was an "imported_object" or a "file".
      let nodeType = "file";
      if (level === 0) {
        nodeType = "root";
      }
  
      // The radial distance increment depends on whether it’s an imported object or not.
      // But we only know if this node is an object if it was specifically flagged. We'll detect that below.
      // For now, assume it's a file if not root. We'll handle objects as separate children.
  
      // Register the current node with a new ID
      const currentId = globalId++;
      const myAngle = parentAngle; // Start aligned with parent's angle (we can offset if needed)
      // Root node => radius=0, otherwise increment from parent's radius
      const myRadius =
        level === 0 ? 0 : parentRadius + distanceFile; // default for .py files
  
      // Convert polar to Cartesian
      const x = myRadius * Math.cos(myAngle);
      const y = myRadius * Math.sin(myAngle);
  
      // Add the node
      nodes.push({
        id: currentId,
        fullName: nodeData.name,
        // shortName is last part of the path
        shortName: nodeData.name.split("/").pop(),
        type: nodeType,
        x,
        y,
      });
  
      // Create a link from parent to me if not root
      if (parentId !== null) {
        links.push({ source: parentId, target: currentId });
      }
  
      // Combine file children (imports) + object children (imported_objects) in a single array
      const fileChildren = nodeData.imports || [];
      const objectChildren = nodeData.imported_objects || [];
      const allChildren = [
        // each child is { name, imports, imported_objects }
        ...fileChildren.map((c) => ({ ...c, __childType: "file" })),
        ...objectChildren.map((objName) => ({
          name: objName,
          imports: [],
          imported_objects: [],
          __childType: "object",
        })),
      ];
  
      if (allChildren.length === 0) return; // Leaf node
  
      // Decide the subrange for children. By default, we do ±45° from myAngle => 90° total
      const subAngle = angleRange || defaultSubAngle; // if I'm root, angleRange=2π, else smaller
      const step = subAngle / allChildren.length;
      let startAngle = myAngle - subAngle / 2;
  
      // For each child, compute a new angle and position
      allChildren.forEach((child) => {
        // Distinguish imported objects from .py files
        let incDistance = distanceFile;
        if (child.__childType === "object") {
          incDistance = distanceObject;
        }
  
        // Center the child within the subrange
        const childAngle = startAngle + step / 2;
        startAngle += step;
  
        // Next level
        const nextLevel = level + 1;
        const childRadius = myRadius + incDistance;
  
        // Recursively assign that child's position
        assignPositions(
          child,
          childAngle,
          subAngle, // children of a child share the same logic => ±45° unless root
          childRadius,
          nextLevel,
          currentId
        );
      });
    }
  
    // ** Entry Point **
  
    // The root node gets the entire 2π angle range
    // level=0 => root => parentRadius=0 => parentAngle=0 => angleRange=2π
    assignPositions(dagData, 0, 2 * Math.PI, 0, 0, null);
  
    return { nodes, links };
  }
  