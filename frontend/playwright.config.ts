import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  use: { baseURL: "http://127.0.0.1:3101", headless: true, channel: process.env.PLAYWRIGHT_CHANNEL },
  webServer: {
    command: "npm run dev -- --port 3101",
    url: "http://127.0.0.1:3101",
    reuseExistingServer: false,
    env: { NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8099" },
    timeout: 120000,
  },
});
