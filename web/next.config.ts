import type { NextConfig } from "next"

// The Python engine serves the data. The browser only ever talks to this app; /api/* is proxied to it.
const ENGINE_URL = process.env.UNPAID_ENGINE_URL ?? "http://127.0.0.1:8000"

const nextConfig: NextConfig = {
  // No floating dev badge: it covers the sidebar and would show in the demo recording.
  devIndicators: false,
  images: {
    // Video thumbnails come straight from YouTube.
    remotePatterns: [{ protocol: "https", hostname: "i.ytimg.com" }],
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${ENGINE_URL}/:path*` }]
  },
}

export default nextConfig
