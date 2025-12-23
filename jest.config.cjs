module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src/ui', '<rootDir>/test/ui'],
  testMatch: ['**/__tests__/**/*.ts?(x)', '**/?(*.)+(spec|test).ts?(x)'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  collectCoverageFrom: [
    'src/ui/**/*.{ts,tsx}',
    '!src/ui/**/*.d.ts',
    '!src/ui/main.tsx',
  ],
  setupFilesAfterEnv: ['<rootDir>/test/ui/setupTests.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/ui/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
};
