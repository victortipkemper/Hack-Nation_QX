const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.AUTOCOMPLY_API_URL ??
          process.env.NEXT_PUBLIC_API_URL ??
          "http://127.0.0.1:8010/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
