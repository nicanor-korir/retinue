/** @type {import('next').NextConfig} */

// NEXT_PUBLIC_* values are inlined at build time. In Docker they arrive as build
// args (see Dockerfile.prod); locally they come from .env.local. The fallbacks
// below are development defaults only — never a deployed host, so that a missing
// build arg fails visibly instead of silently pointing at someone else's server.
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || API_URL.replace(/^http/, 'ws');

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone', // For Docker deployment
  env: {
    NEXT_PUBLIC_API_URL: API_URL,
    NEXT_PUBLIC_WS_URL: WS_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
