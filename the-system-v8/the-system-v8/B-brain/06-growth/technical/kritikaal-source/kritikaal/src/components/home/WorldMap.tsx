"use client";

import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";
import { motion } from "framer-motion";
import Markers from "./Markers";
import FlowLines from "./FlowLines";

// GeoJSON URL for world map topology
const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Destination hubs
const CHINA = {
  name: "CHINA",
  coordinates: [104.1954, 35.8617] as [number, number],
  color: "#ef4444", // Red
  size: "large" as const,
  label: "CHINA",
};

const INDIA = {
  name: "INDIA",
  coordinates: [78.9629, 20.5937] as [number, number],
  color: "#22c55e", // Green
  size: "large" as const,
  label: "INDIA",
};

// Source countries with accurate coordinates
const SOURCE_COUNTRIES = [
  {
    name: "NETHERLANDS",
    coordinates: [5.2913, 52.1326] as [number, number],
    color: "#94a3b8",
    size: "small" as const,
    label: "Netherlands",
  },
  {
    name: "GERMANY",
    coordinates: [10.4515, 51.1657] as [number, number],
    color: "#94a3b8",
    size: "small" as const,
    label: "Germany",
  },
  {
    name: "FRANCE",
    coordinates: [2.2137, 46.2276] as [number, number],
    color: "#94a3b8",
    size: "small" as const,
    label: "France",
  },
  {
    name: "ITALY",
    coordinates: [12.5674, 41.8719] as [number, number],
    color: "#94a3b8",
    size: "small" as const,
    label: "Italy",
  },
  {
    name: "AUSTRALIA",
    coordinates: [133.7751, -25.2744] as [number, number],
    color: "#94a3b8",
    size: "small" as const,
    label: "Australia",
  },
];

const WorldMap = () => {
  // Create flow lines from each source to both destinations
  const flows = [
    // Flows to China (Red)
    ...SOURCE_COUNTRIES.map((source) => ({
      from: source.coordinates,
      to: CHINA.coordinates,
      color: CHINA.color,
      name: `${source.name}-CHINA`,
    })),
    // Flows to India (Green)
    ...SOURCE_COUNTRIES.map((source) => ({
      from: source.coordinates,
      to: INDIA.coordinates,
      color: INDIA.color,
      name: `${source.name}-INDIA`,
    })),
  ];

  const allMarkers = [CHINA, INDIA, ...SOURCE_COUNTRIES];

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl overflow-hidden shadow-2xl border border-slate-700/50">
      <motion.div
        initial={{ opacity: 1, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full h-full"
      >
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 150,
            center: [60, 20],
          }}
          width={800}
          height={450}
          style={{
            width: "100%",
            height: "100%",
          }}
        >
          {/* World map geography */}
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#1e293b"
                  stroke="#334155"
                  strokeWidth={0.5}
                  style={{
                    default: {
                      fill: "#1e293b",
                      stroke: "#334155",
                      strokeWidth: 0.5,
                      outline: "none",
                    },
                    hover: {
                      fill: "#334155",
                      stroke: "#475569",
                      strokeWidth: 0.5,
                      outline: "none",
                    },
                    pressed: {
                      fill: "#334155",
                      stroke: "#475569",
                      strokeWidth: 0.5,
                      outline: "none",
                    },
                  }}
                />
              ))
            }
          </Geographies>

          {/* Flow lines */}
          <FlowLines flows={flows} />

          {/* Markers */}
          <Markers markers={allMarkers} />
        </ComposableMap>
      </motion.div>

      {/* Legend */}
      <div className="absolute bottom-6 left-6 bg-slate-900/90 backdrop-blur-sm border border-slate-700/50 rounded-lg px-4 py-3 shadow-lg">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
            <span className="text-slate-200 font-medium">China Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <span className="text-slate-200 font-medium">India Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-slate-400" />
            <span className="text-slate-200 font-medium">Source Countries</span>
          </div>
        </div>
      </div>

      {/* Title overlay */}
      <div className="absolute top-6 left-6 right-6">
        <motion.div
          initial={{ opacity: 1, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <h3 className="text-2xl font-serif font-medium text-white mb-1 tracking-tight">
            Global Manufacturing Flow
          </h3>
          <p className="text-slate-400 text-sm font-medium">
            Visualizing the shift from China to India
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default WorldMap;

