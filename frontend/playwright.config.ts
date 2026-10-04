import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  expect: { timeout: 15000 },
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:8100",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command:
      "WORK2030_DB=runtime/e2e.sqlite ANIMATOR_TOKEN=test-secret ../.venv/bin/uvicorn work2030.api:app --host 127.0.0.1 --port 8100",
    url: "http://127.0.0.1:8100/api/health",
    reuseExistingServer: false,
    timeout: 15000,
  },
});
