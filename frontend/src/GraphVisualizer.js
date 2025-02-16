import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import yaml from "js-yaml";

const GraphVisualizer = () => {
  const svgRef = useRef(null);
  const [data, setData] = useState(null);

  // Load and parse the YAML file on component mount
  useEffect(() => {
    fetch(process.env.PUBLIC_URL + "/file_tree.yaml")
      .then((response) => response.text())
      .then((text) => {
        const parsedData = yaml.load(text);
        setData(parsedData);
      })
      .catch((err) => console.error("Failed to load YAML:", err));
  }, []);

  // Create the D3 visualization once data is available
  useEffect(() => {
    if (!data) return;

    // Flatten the tree structure into nodes and links
    let nodes = [];
    let links = [];
    let id = 0;

    function traverse(tree, parentId = null) {
      const currentId = id++;
      nodes.push({
        id: currentId,
        name: tree.name,
        type: "folder", // Folders by default
      });

      if (parentId !== null) {
        links.push({ source: parentId, target: currentId });
      }

      // Add files as leaf nodes
      if (tree.files) {
        tree.files.forEach((file) => {
          const fileId = id++;
          nodes.push({
            id: fileId,
            name: file,
            type: "file",
          });
          links.push({ source: currentId, target: fileId });
        });
      }

      // Traverse subfolders
      if (tree.folders) {
        tree.folders.forEach((folder) => {
          traverse(folder, currentId);
        });
      }
    }
    traverse(data);

    // Create the SVG container and set up zooming/panning behavior
    const width = window.innerWidth;
    const height = window.innerHeight;

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .call(
        d3
          .zoom()
          .scaleExtent([0.1, 4]) // Zoom range
          .on("zoom", (event) => {
            g.attr("transform", event.transform);
          })
      );

    const g = svg.append("g");

    // Simulation for force-directed graph
    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-50)) // Lower repulsion for slow, heavy movement
      .force("center", d3.forceCenter(width / 2, height / 2))
      .alphaDecay(0.02); // Lower decay for slower movement

    // Draw links
    const link = g
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-width", 2);

    // Draw nodes
    const node = g
        .selectAll("circle")
        .data(nodes)
        .enter()
        .append("circle")
        .attr("r", 10)
        .attr("fill", (d) => (d.id === 0 ? "black" : d.type === "folder" ? "#f8cb72" : "#72aef8")) // Root (black), Folder (orange), File (blue)
        .attr("stroke", (d) => (d.id === 0 ? "black" : d.type === "folder" ? "orange" : "blue")) // Root (black), Folder (orange), File (blue)
        .attr("stroke-width", 3)
        .call(
            d3
            .drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
    );

    // Add labels
    const label = g
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .text((d) => d.name)
      .attr("font-size", 12)
      .attr("dx", 15)
      .attr("dy", ".35em");

    // Simulation tick update
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

      label.attr("x", (d) => d.x).attr("y", (d) => d.y);
    });

    // Drag handlers
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Handle window resize for responsive graph size
    const handleResize = () => {
      const newWidth = window.innerWidth;
      const newHeight = window.innerHeight;

      svg.attr("width", newWidth).attr("height", newHeight);
      simulation.force("center", d3.forceCenter(newWidth / 2, newHeight / 2));
      simulation.alpha(0.3).restart(); // Restart simulation on resize
    };

    window.addEventListener("resize", handleResize);

    // Cleanup on component unmount
    return () => {
      window.removeEventListener("resize", handleResize);
      simulation.stop();
    };
  }, [data]);

  return <svg ref={svgRef}></svg>;
};

export default GraphVisualizer;
