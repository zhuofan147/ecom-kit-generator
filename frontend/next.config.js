/** @type {import('next').NextConfig} */
const os = require("os");

const localNetworkOrigins = Object.values(os.networkInterfaces())
  .flat()
  .filter((item) => item?.family === "IPv4" && !item.internal)
  .map((item) => item.address);

const nextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["127.0.0.1", "localhost", ...localNetworkOrigins],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "no-cache, no-store, must-revalidate",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
