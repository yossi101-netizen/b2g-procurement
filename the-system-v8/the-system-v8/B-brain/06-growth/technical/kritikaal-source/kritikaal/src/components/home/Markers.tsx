"use client";

import { Marker } from "react-simple-maps";
import { motion } from "framer-motion";

interface MarkerData {
  name: string;
  coordinates: [number, number];
  color: string;
  size: "large" | "small";
  label: string;
}

interface MarkersProps {
  markers: MarkerData[];
}

const Markers = ({ markers }: MarkersProps) => {
  return (
    <>
      {markers.map((marker, index) => (
        <g key={marker.name}>
          {/* Outer glow */}
          <Marker coordinates={marker.coordinates}>
            <motion.circle
              r={marker.size === "large" ? 20 : 12}
              fill={marker.color}
              fillOpacity={0.1}
              animate={{
                r: marker.size === "large" ? [20, 28, 20] : [12, 18, 12],
                fillOpacity: [0.1, 0.25, 0.1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: index * 0.2,
              }}
            />
          </Marker>

          {/* Middle glow */}
          <Marker coordinates={marker.coordinates}>
            <motion.circle
              r={marker.size === "large" ? 12 : 7}
              fill={marker.color}
              fillOpacity={0.3}
              animate={{
                r: marker.size === "large" ? [12, 18, 12] : [7, 11, 7],
                fillOpacity: [0.3, 0.5, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: index * 0.2,
              }}
            />
          </Marker>

          {/* Core marker */}
          <Marker coordinates={marker.coordinates}>
            <circle
              r={marker.size === "large" ? 6 : 3.5}
              fill={marker.color}
              stroke="white"
              strokeWidth={marker.size === "large" ? 2 : 1}
            />
          </Marker>

          {/* Label */}
          <Marker coordinates={marker.coordinates}>
            <text
              textAnchor="middle"
              y={marker.size === "large" ? -25 : -18}
              style={{
                fontFamily: "system-ui, -apple-system, sans-serif",
                fontSize: marker.size === "large" ? "14px" : "11px",
                fontWeight: marker.size === "large" ? 700 : 600,
                fill: "#ffffff",
                stroke: "#000000",
                strokeWidth: marker.size === "large" ? 3 : 2.5,
                paintOrder: "stroke",
                letterSpacing: marker.size === "large" ? "0.5px" : "0.3px",
              }}
            >
              {marker.label}
            </text>
          </Marker>
        </g>
      ))}
    </>
  );
};

export default Markers;