import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const configDir = path.dirname(fileURLToPath(import.meta.url));
const monorepoRoot = path.join(configDir, "../..");

const nextConfig: NextConfig = {
  transpilePackages: ["healthcore-testing"],
  async rewrites() {
    const backend = process.env.HC_API_INTERNAL_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";
    return [
      {
        source: "/backend/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
  turbopack: {
    // Keep resolution at the npm workspaces root so `healthcore-testing` stays linked.
    root: monorepoRoot,
  },
  outputFileTracingRoot: monorepoRoot,
};

export default nextConfig;
