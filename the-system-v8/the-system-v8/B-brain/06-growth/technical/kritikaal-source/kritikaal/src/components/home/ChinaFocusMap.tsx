"use client";

import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Line,
} from "react-simple-maps";
import { motion } from "framer-motion";
import { useState } from "react";

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// China coordinates
const CHINA = {
  coordinates: [104.1954, 35.8617] as [number, number],
  name: "CHINA",
};

// Source countries with enhanced data
const SOURCES = [
  { name: "Netherlands", coordinates: [5.2913, 52.1326] as [number, number] },
  { name: "Germany", coordinates: [10.4515, 51.1657] as [number, number] },
  { name: "France", coordinates: [2.2137, 46.2276] as [number, number] },
  { name: "Italy", coordinates: [12.5674, 41.8719] as [number, number] },
  { name: "Australia", coordinates: [133.7751, -25.2744] as [number, number] },
];

const ChinaFocusMap = () => {
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [hoveredLine, setHoveredLine] = useState<number | null>(null);

  return (
    <div className="w-full h-full relative">
      <motion.div
        initial={{ opacity: 1, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="w-full h-full"
      >
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 180,
            center: [60, 25],
          }}
          width={800}
          height={500}
          style={{
            width: "100%",
            height: "100%",
          }}
        >
          <defs>
            {/* Enhanced glow filter for China */}
            <filter id="china-glow-enhanced" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="8" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Enhanced line glow */}
            <filter id="line-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Premium red gradient for flow lines */}
            <linearGradient id="china-flow-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="50%" stopColor="#ef4444" stopOpacity={0.8} />
              <stop offset="100%" stopColor="#dc2626" stopOpacity={1} />
            </linearGradient>

            {/* Radial gradient for markers */}
            <radialGradient id="marker-gradient">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={1} />
              <stop offset="100%" stopColor="#dc2626" stopOpacity={0.8} />
            </radialGradient>

            {/* Premium navy gradient background */}
            <linearGradient id="map-bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0f172a" />
              <stop offset="50%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
          </defs>

          {/* Premium gradient background */}
          <rect width="800" height="500" fill="url(#map-bg-gradient)" />

          {/* World geography with improved styling */}
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const isChina = geo.properties.name === "China";
                const isHovered = hoveredCountry === geo.properties.name;
                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    onMouseEnter={() => setHoveredCountry(geo.properties.name)}
                    onMouseLeave={() => setHoveredCountry(null)}
                    fill={isChina ? "#ef4444" : "#1e293b"}
                    stroke={isChina ? "#dc2626" : "#334155"}
                    strokeWidth={isChina ? 1.5 : 0.4}
                    style={{
                      default: {
                        fill: isChina ? "#ef4444" : "#1e293b",
                        stroke: isChina ? "#dc2626" : "#334155",
                        strokeWidth: isChina ? 1.5 : 0.4,
                        outline: "none",
                        filter: isChina ? "url(#china-glow-enhanced)" : "none",
                        transition: "all 0.3s ease",
                      },
                      hover: {
                        fill: isChina ? "#dc2626" : "#334155",
                        stroke: isChina ? "#b91c1c" : "#475569",
                        strokeWidth: isChina ? 2 : 0.5,
                        outline: "none",
                        filter: isChina ? "url(#china-glow-enhanced)" : "none",
                        transition: "all 0.3s ease",
                      },
                      pressed: {
                        fill: isChina ? "#dc2626" : "#334155",
                        stroke: isChina ? "#b91c1c" : "#475569",
                        strokeWidth: isChina ? 2 : 0.5,
                        outline: "none",
                      },
                    }}
                  />
                );
              })
            }
          </Geographies>

          {/* Premium flow lines with animated dots */}
          {SOURCES.map((source, index) => (
            <g 
              key={`flow-${index}`}
              onMouseEnter={() => setHoveredLine(index)}
              onMouseLeave={() => setHoveredLine(null)}
            >
              {/* Outer glow layer */}
              <Line
                from={source.coordinates}
                to={CHINA.coordinates}
                stroke="#ef4444"
                strokeWidth={hoveredLine === index ? 4 : 3}
                strokeOpacity={hoveredLine === index ? 0.4 : 0.2}
                filter="url(#line-glow)"
                strokeLinecap="round"
              />
              
              {/* Main animated line */}
              <motion.g
                initial={{ pathLength: 0, opacity: 1 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 2, delay: index * 0.2, ease: "easeInOut" }}
              >
                <Line
                  from={source.coordinates}
                  to={CHINA.coordinates}
                  stroke="url(#china-flow-gradient)"
                  strokeWidth={hoveredLine === index ? 2.5 : 2}
                  strokeLinecap="round"
                  strokeOpacity={hoveredLine === index ? 1 : 0.8}
                />
              </motion.g>

              {/* Animated glowing particles */}
              <motion.g
                initial={{ strokeDashoffset: 0 }}
                animate={{ strokeDashoffset: -40 }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "linear",
                  delay: index * 0.2,
                }}
              >
                <Line
                  from={source.coordinates}
                  to={CHINA.coordinates}
                  stroke="#ef4444"
                  strokeWidth={hoveredLine === index ? 3 : 2.5}
                  strokeLinecap="round"
                  strokeDasharray="8 16"
                  strokeOpacity={hoveredLine === index ? 0.9 : 0.7}
                  filter="url(#line-glow)"
                />
              </motion.g>

              {/* Moving glowing dots */}
              {[0, 0.33, 0.66].map((offset, dotIndex) => (
                <motion.circle
                  key={`dot-${index}-${dotIndex}`}
                  r={hoveredLine === index ? 3 : 2}
                  fill="#ef4444"
                  filter="url(#line-glow)"
                  initial={{ opacity: 1 }}
                  animate={{
                    opacity: [0, 1, 1, 0],
                    cx: [source.coordinates[0], CHINA.coordinates[0]],
                    cy: [source.coordinates[1], CHINA.coordinates[1]],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: index * 0.2 + offset,
                  }}
                />
              ))}
            </g>
          ))}

          {/* Enhanced source markers with ripple effect */}
          {SOURCES.map((source, index) => (
            <Marker key={`source-${index}`} coordinates={source.coordinates}>
              {/* Outer ripple effect */}
              <motion.circle
                r={0}
                fill="none"
                stroke="#94a3b8"
                strokeWidth={2}
                strokeOpacity={0}
                initial={{ r: 0, strokeOpacity: 0 }}
                animate={{ 
                  r: [6, 14],
                  strokeOpacity: [0.6, 0]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeOut",
                  delay: index * 0.3,
                }}
              />
              
              {/* Main marker */}
              <motion.circle
                r={5}
                fill="url(#marker-gradient)"
                stroke="#ffffff"
                strokeWidth={2}
                initial={{ scale: 0, opacity: 1 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
              />
              
              {/* Pulsing inner core */}
              <motion.circle
                r={2}
                fill="#ffffff"
                animate={{
                  opacity: [1, 0.5, 1],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: index * 0.15,
                }}
              />
            </Marker>
          ))}

          {/* China hub marker with enhanced pulsing effect */}
          <Marker coordinates={CHINA.coordinates}>
            {/* Outermost ripple */}
            <motion.circle
              r={20}
              fill="#ef4444"
              fillOpacity={0}
              stroke="#ef4444"
              strokeWidth={2}
              strokeOpacity={0.3}
              animate={{
                r: [20, 35],
                strokeOpacity: [0.5, 0],
              }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "easeOut",
              }}
            />
            
            {/* Middle pulse */}
            <motion.circle
              r={20}
              fill="#ef4444"
              fillOpacity={0.15}
              animate={{
                r: [20, 28, 20],
                fillOpacity: [0.15, 0.35, 0.15],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            {/* Inner glow */}
            <motion.circle
              r={12}
              fill="#ef4444"
              fillOpacity={0.5}
              filter="url(#china-glow-enhanced)"
              animate={{
                r: [12, 16, 12],
                fillOpacity: [0.5, 0.7, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            {/* Core marker */}
            <circle 
              r={7} 
              fill="#ef4444" 
              stroke="#ffffff" 
              strokeWidth={2.5}
              filter="url(#line-glow)"
            />
            
            {/* Bright center */}
            <circle r={3} fill="#ffffff" opacity={0.9} />
          </Marker>

          {/* China label with improved typography */}
          <Marker coordinates={CHINA.coordinates}>
            <motion.text
              textAnchor="middle"
              y={-28}
              initial={{ opacity: 1, y: -20 }}
              animate={{ opacity: 1, y: -28 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              style={{
                fontFamily: "Inter, system-ui, -apple-system, sans-serif",
                fontSize: "15px",
                fontWeight: 800,
                fill: "#ffffff",
                stroke: "#000000",
                strokeWidth: 4,
                paintOrder: "stroke",
                letterSpacing: "2px",
                textTransform: "uppercase",
              }}
            >
              CHINA
            </motion.text>
          </Marker>
        </ComposableMap>
      </motion.div>
    </div>
  );
};

export default ChinaFocusMap;

