"use client";

import { Line } from "react-simple-maps";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface FlowLineData {
  from: [number, number];
  to: [number, number];
  color: string;
  name: string;
}

interface FlowLinesProps {
  flows: FlowLineData[];
}

// Function to create curved path between two coordinates
const createCurvePath = (from: [number, number], to: [number, number]): string => {
  const [x1, y1] = from;
  const [x2, y2] = to;

  // Calculate control point for the curve (arc upward)
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  
  // Calculate distance to determine curve intensity
  const dx = x2 - x1;
  const dy = y2 - y1;
  const distance = Math.sqrt(dx * dx + dy * dy);
  
  // Create arc by offsetting control points
  const offset = distance * 0.25; // Curve intensity
  const controlX = midX;
  const controlY = midY - offset;

  return `M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`;
};

const FlowLines = ({ flows }: FlowLinesProps) => {
  const [animatedFlows, setAnimatedFlows] = useState<FlowLineData[]>([]);

  useEffect(() => {
    // Stagger the appearance of flow lines
    flows.forEach((flow, index) => {
      setTimeout(() => {
        setAnimatedFlows((prev) => [...prev, flow]);
      }, index * 150);
    });
  }, [flows]);

  return (
    <>
      {animatedFlows.map((flow, index) => {
        const pathId = `flow-${index}`;
        const gradientId = `gradient-${index}`;

        return (
          <g key={pathId}>
            {/* Define gradient for the flow line */}
            <defs>
              <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={flow.color} stopOpacity={0.1} />
                <stop offset="50%" stopColor={flow.color} stopOpacity={0.6} />
                <stop offset="100%" stopColor={flow.color} stopOpacity={0.9} />
              </linearGradient>

              {/* Glow filter */}
              <filter id={`glow-${index}`} x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Outer glow path */}
            <motion.path
              d={createCurvePath(flow.from, flow.to)}
              fill="none"
              stroke={flow.color}
              strokeWidth={3}
              strokeOpacity={0.2}
              filter={`url(#glow-${index})`}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{
                duration: 1.5,
                ease: "easeInOut",
                delay: index * 0.1,
              }}
            />

            {/* Main flow line */}
            <motion.path
              d={createCurvePath(flow.from, flow.to)}
              fill="none"
              stroke={`url(#${gradientId})`}
              strokeWidth={2}
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{
                duration: 1.5,
                ease: "easeInOut",
                delay: index * 0.1,
              }}
            />

            {/* Animated particles along the path */}
            <motion.path
              d={createCurvePath(flow.from, flow.to)}
              fill="none"
              stroke={flow.color}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeDasharray="8 20"
              initial={{ strokeDashoffset: 0 }}
              animate={{ strokeDashoffset: -28 }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "linear",
                delay: index * 0.1,
              }}
            />
          </g>
        );
      })}
    </>
  );
};

export default FlowLines;

