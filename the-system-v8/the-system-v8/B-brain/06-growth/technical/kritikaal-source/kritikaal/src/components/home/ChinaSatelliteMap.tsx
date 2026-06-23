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

// High-quality world map with Natural Earth data
const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Accurate geographic coordinates
const CHINA = {
  coordinates: [104.1954, 35.8617] as [number, number],
  name: "CHINA",
};

// Source countries with accurate coordinates
const SOURCES = [
  { name: "Spain", coordinates: [-3.7492, 40.4637] as [number, number] },
  { name: "Italy", coordinates: [12.5674, 41.8719] as [number, number] },
  { name: "Germany", coordinates: [10.4515, 51.1657] as [number, number] },
  { name: "France", coordinates: [2.2137, 46.2276] as [number, number] },
  { name: "UK", coordinates: [-0.1276, 51.5074] as [number, number] },
  { name: "Australia", coordinates: [133.7751, -25.2744] as [number, number] },
];

const ChinaSatelliteMap = () => {
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [hoveredLine, setHoveredLine] = useState<number | null>(null);

  return (
    <div className="w-full h-full relative">
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{
          scale: 240,
          center: [60, 20],
        }}
        width={800}
        height={600}
        style={{
          width: "100%",
          height: "100%",
        }}
      >
        <defs>
          {/* Realistic ocean gradient - sky blue */}
          <linearGradient id="ocean-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#4A90E2" />
            <stop offset="100%" stopColor="#2E5F8A" />
          </linearGradient>

          {/* Enhanced glow for China */}
          <filter id="china-glow-satellite" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Line glow for flow lines */}
          <filter id="line-glow-red" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Red flow gradient */}
          <linearGradient id="red-flow-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
            <stop offset="50%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#dc2626" stopOpacity={1} />
          </linearGradient>
        </defs>

        {/* Realistic ocean background */}
        <rect width="800" height="600" fill="url(#ocean-gradient)" />

        {/* World geography with realistic colors */}
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const isChina = geo.properties.name === "China";
              const isSource = SOURCES.some(s => s.name === geo.properties.name);
              const isHovered = hoveredCountry === geo.properties.name;
              
              // Realistic land colors based on region
              let fillColor = "#7CB342"; // Default green land
              
              // Desert regions
              if (["Algeria", "Libya", "Egypt", "Saudi Arabia", "Mali", "Niger", "Chad", "Sudan", "Mauritania"].includes(geo.properties.name)) {
                fillColor = "#C19A6B"; // Brown desert
              }
              // Polar regions
              if (["Greenland", "Iceland"].includes(geo.properties.name)) {
                fillColor = "#E8F5E9"; // White/pale for ice
              }
              // China - highlighted
              if (isChina) {
                fillColor = "#ef4444"; // Red for China
              }
              // Source countries - subtle highlight
              if (isSource) {
                fillColor = "#90CAF9"; // Light blue for sources
              }

              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onMouseEnter={() => setHoveredCountry(geo.properties.name)}
                  onMouseLeave={() => setHoveredCountry(null)}
                  fill={fillColor}
                  stroke={isChina ? "#dc2626" : "#2E7D32"}
                  strokeWidth={isChina ? 2 : 0.5}
                  style={{
                    default: {
                      fill: fillColor,
                      stroke: isChina ? "#dc2626" : "#2E7D32",
                      strokeWidth: isChina ? 2 : 0.5,
                      outline: "none",
                      filter: isChina ? "url(#china-glow-satellite)" : "none",
                      transition: "all 0.3s ease",
                    },
                    hover: {
                      fill: isChina ? "#dc2626" : isSource ? "#64B5F6" : fillColor,
                      stroke: isChina ? "#b91c1c" : "#1B5E20",
                      strokeWidth: isChina ? 2.5 : 0.7,
                      outline: "none",
                      filter: isChina ? "url(#china-glow-satellite)" : "none",
                      transition: "all 0.3s ease",
                      cursor: "pointer",
                    },
                    pressed: {
                      fill: fillColor,
                      outline: "none",
                    },
                  }}
                />
              );
            })
          }
        </Geographies>

        {/* Curved flow lines to China */}
        {SOURCES.map((source, index) => (
          <g 
            key={`flow-${index}`}
            onMouseEnter={() => setHoveredLine(index)}
            onMouseLeave={() => setHoveredLine(null)}
          >
            {/* Outer glow */}
            <Line
              from={source.coordinates}
              to={CHINA.coordinates}
              stroke="#ef4444"
              strokeWidth={hoveredLine === index ? 5 : 4}
              strokeOpacity={hoveredLine === index ? 0.5 : 0.3}
              filter="url(#line-glow-red)"
              strokeLinecap="round"
            />
            
            {/* Main animated line */}
            <motion.g
              initial={{ pathLength: 0, opacity: 1 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 2.5, delay: index * 0.3, ease: "easeInOut" }}
            >
              <Line
                from={source.coordinates}
                to={CHINA.coordinates}
                stroke="url(#red-flow-gradient)"
                strokeWidth={hoveredLine === index ? 3 : 2.5}
                strokeLinecap="round"
                strokeOpacity={hoveredLine === index ? 1 : 0.9}
              />
            </motion.g>

            {/* Animated glowing particles */}
            <motion.g
              initial={{ strokeDashoffset: 0 }}
              animate={{ strokeDashoffset: -50 }}
              transition={{
                duration: 3.5,
                repeat: Infinity,
                ease: "linear",
                delay: index * 0.3,
              }}
            >
              <Line
                from={source.coordinates}
                to={CHINA.coordinates}
                stroke="#ef4444"
                strokeWidth={hoveredLine === index ? 3.5 : 3}
                strokeLinecap="round"
                strokeDasharray="10 20"
                strokeOpacity={hoveredLine === index ? 1 : 0.8}
                filter="url(#line-glow-red)"
              />
            </motion.g>

            {/* Moving glowing dots */}
            {[0, 0.4, 0.7].map((offset, dotIndex) => (
              <motion.circle
                key={`dot-${index}-${dotIndex}`}
                r={hoveredLine === index ? 3.5 : 2.5}
                fill="#ff6b6b"
                filter="url(#line-glow-red)"
                initial={{ opacity: 1 }}
                animate={{
                  opacity: [0, 1, 1, 0],
                  cx: [source.coordinates[0], CHINA.coordinates[0]],
                  cy: [source.coordinates[1], CHINA.coordinates[1]],
                }}
                transition={{
                  duration: 3.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: index * 0.3 + offset * 2,
                }}
              />
            ))}
          </g>
        ))}

        {/* Source country markers */}
        {SOURCES.map((source, index) => (
          <Marker key={`source-${index}`} coordinates={source.coordinates}>
            {/* Ripple effect */}
            <motion.circle
              r={0}
              fill="none"
              stroke="#ef4444"
              strokeWidth={2}
              strokeOpacity={0}
              animate={{ 
                r: [8, 18],
                strokeOpacity: [0.7, 0]
              }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "easeOut",
                delay: index * 0.4,
              }}
            />
            
            {/* Main marker */}
            <motion.circle
              r={6}
              fill="#ff6b6b"
              stroke="#ffffff"
              strokeWidth={2.5}
              initial={{ scale: 0, opacity: 1 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.6, delay: index * 0.2 }}
            />
            
            {/* Inner glow */}
            <motion.circle
              r={3}
              fill="#ffffff"
              animate={{
                opacity: [1, 0.6, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: index * 0.2,
              }}
            />

            {/* Country label */}
            <text
              textAnchor="middle"
              y={-16}
              style={{
                fontFamily: "Inter, system-ui, sans-serif",
                fontSize: "11px",
                fontWeight: 600,
                fill: "#ffffff",
                stroke: "#000000",
                strokeWidth: 3,
                paintOrder: "stroke",
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}
            >
              {source.name}
            </text>
          </Marker>
        ))}

        {/* China hub marker */}
        <Marker coordinates={CHINA.coordinates}>
          {/* Outermost ripple */}
          <motion.circle
            r={25}
            fill="none"
            stroke="#ef4444"
            strokeWidth={3}
            strokeOpacity={0}
            animate={{
              r: [25, 45],
              strokeOpacity: [0.6, 0],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
          
          {/* Middle pulse */}
          <motion.circle
            r={25}
            fill="#ef4444"
            fillOpacity={0.2}
            animate={{
              r: [25, 35, 25],
              fillOpacity: [0.2, 0.4, 0.2],
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          {/* Inner glow */}
          <motion.circle
            r={15}
            fill="#ef4444"
            fillOpacity={0.6}
            filter="url(#china-glow-satellite)"
            animate={{
              r: [15, 20, 15],
              fillOpacity: [0.6, 0.8, 0.6],
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          {/* Core marker */}
          <circle 
            r={9} 
            fill="#ef4444" 
            stroke="#ffffff" 
            strokeWidth={3}
            filter="url(#line-glow-red)"
          />
          
          {/* Bright center */}
          <circle r={4} fill="#ffffff" opacity={0.95} />
        </Marker>

        {/* China label */}
        <Marker coordinates={CHINA.coordinates}>
          <motion.text
            textAnchor="middle"
            y={-35}
            initial={{ opacity: 1, y: -28 }}
            animate={{ opacity: 1, y: -35 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            style={{
              fontFamily: "Inter, system-ui, sans-serif",
              fontSize: "16px",
              fontWeight: 900,
              fill: "#ffffff",
              stroke: "#000000",
              strokeWidth: 4.5,
              paintOrder: "stroke",
              letterSpacing: "2.5px",
              textTransform: "uppercase",
            }}
          >
            CHINA
          </motion.text>
        </Marker>
      </ComposableMap>
    </div>
  );
};

export default ChinaSatelliteMap;

