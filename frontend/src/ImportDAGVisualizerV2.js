import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import yaml from "js-yaml";
import { radialLayout } from "./radialLayout"; // <-- Import the separate module

const ImportDAGVisualizerV2 = () => {
  const svgRef = useRef(null);
  const [data, setData] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null); // For displaying full path on click

  // 1. Load and parse the import DAG YAML file on component mount
  useEffect(() => {
    fetch(process.env.PUBLIC_URL + "/import_dag.yaml")
      .then((response) => response.text())
      .then((text) => {
        const parsedData = yaml.load(text);
        setData(parsedData);
      })
      .catch((err) => console.error("Failed to load YAML:", err));
  }, []);

  // 2. Build and render the radial graph once data is available
  useEffect(() => {
    if (!data) return;

    // Use our radialLayout function to get positions & links
    const { nodes, links } = radialLayout(data);

    // Set up the SVG dimensions and attach zoom/pan behavior
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

    // The main group where nodes and links are drawn
    const g = svg.append("g");

    // No force layout needed for the initial positions, but if you want to allow minimal "jiggle," you can set a low alpha.
    // We'll do a simple simulation that starts from the radial layout and keeps them near their positions.

    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(10))
      .force("charge", d3.forceManyBody().strength(-20))
      .on("tick", () => {
        link
          .attr("x1", (d) => d.source.x)
          .attr("y1", (d) => d.source.y)
          .attr("x2", (d) => d.target.x)
          .attr("y2", (d) => d.target.y);

        node
          .attr("cx", (d) => d.x)
          .attr("cy", (d) => d.y);

        label
          .attr("x", (d) => d.x)
          .attr("y", (d) => d.y);
      });

    // Draw links
    const link = g
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-width", 2);

    // Draw nodes (circles)
    const node = g
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => {
        if (d.type === "root") return "black";
        if (d.type === "object") return "#f77f7f"; // Red fill for imported objects
        return "#72aef8"; // Blue fill for scripts
      })
      .attr("stroke", (d) => {
        if (d.type === "root") return "black";
        if (d.type === "object") return "red";
        return "blue"; // script
      })
      .attr("stroke-width", 3)
      // Click handler: update selectedFile state to show full path
      .on("click", (event, d) => {
        setSelectedFile(d.fullName);
        event.stopPropagation(); // Prevent zoom/pan from also firing
      })
      // (Optional) Enable dragging if you want users to move nodes
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    // Labels for nodes
    const label = g
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .text((d) => d.shortName)
      .attr("font-size", 12)
      .attr("dx", 15)
      .attr("dy", ".35em");

    // Basic drag handlers if you want minimal force
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

    // Handle window resizing
    const handleResize = () => {
      const newWidth = window.innerWidth;
      const newHeight = window.innerHeight;
      svg.attr("width", newWidth).attr("height", newHeight);
    };

    window.addEventListener("resize", handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener("resize", handleResize);
      simulation.stop();
    };
  }, [data]);

  // 3. Display the full path in the top-right corner if a file is selected
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          backgroundColor: "rgba(255, 255, 255, 0.7)",
          padding: "8px",
          borderRadius: "4px",
          border: "1px solid #ccc",
        }}
      >
        {selectedFile ? <div>Full Path: {selectedFile}</div> : "Click a node to see its path"}
      </div>
      <svg ref={svgRef}></svg>
    </>
  );
};

export default ImportDAGVisualizerV2;
