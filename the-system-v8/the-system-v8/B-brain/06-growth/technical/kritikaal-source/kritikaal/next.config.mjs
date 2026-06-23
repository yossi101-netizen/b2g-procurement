/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export', // Removed to enable SSR, API Routes, and Edge Middleware (Fixes Failure #1)
  trailingSlash: true,
  // Allow importing images from external domains
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'flagcdn.com',
      },
    ],
    // Allow unoptimized images for static export compatibility
    unoptimized: true,
  },
  // Transpile specific packages that need it
  transpilePackages: ['framer-motion', 'lucide-react', 'react-icons'],
  // Webpack config for handling SVGs and other assets
  webpack: (config) => {
    return config;
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
