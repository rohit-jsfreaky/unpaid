import type { NextConfig } from "next"

// The Python engine serves the data under /api. The browser only ever calls /api/* on this same origin:
// locally this app proxies it to the engine; on Vercel the top-level rewrite in vercel.json sends it to the engine
// service before it reaches this app.
const ENGINE_URL = process.env.UNPAID_ENGINE_URL ?? "http://127.0.0.1:8000"

const nextConfig: NextConfig = {
  // No floating dev badge: it covers the sidebar and would show in the demo recording.
  devIndicators: false,
  images: {
    // Video thumbnails come straight from YouTube.
    remotePatterns: [{ protocol: "https", hostname: "i.ytimg.com" }],
  },
  async rewrites() {
    if (process.env.VERCEL) return []
    return [{ source: "/api/:path*", destination: `${ENGINE_URL}/api/:path*` }]
  },
}

export default nextConfig
