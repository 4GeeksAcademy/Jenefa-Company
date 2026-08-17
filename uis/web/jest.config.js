/** @type {import('jest').Config} */
const config = {
  testEnvironment: "jsdom",
  roots: ["<rootDir>/src"],
  testMatch: ["**/__tests__/**/*.test.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: {
          module: "commonjs",
          moduleResolution: "node",
          esModuleInterop: true,
          isolatedModules: true,
          jsx: "react-jsx",
          paths: { "@/*": ["./src/*"] },
        },
      },
    ],
  },
  collectCoverageFrom: [
    "src/lib/authStorage.ts",
    "src/lib/userFacingError.ts",
    "src/lib/api.ts",
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "text-summary"],
  clearMocks: true,
};

module.exports = config;
