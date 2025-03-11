/**
 * Application configuration
 * Centralizes all configuration values and environment variables
 */
interface Config {
  api: {
    baseUrl: string;
    path: string;
  };
  polling: {
    interval: number; // in milliseconds
  };
}

// Get environment variables safely
const getEnvVar = (key: string, defaultValue: string): string => {
  // For Vite, we would use import.meta.env.VITE_API_BASE_URL
  // For Create React App, we would use process.env.REACT_APP_API_BASE_URL
  // Since we're not sure which one is configured, we'll use a fallback approach
  return (
    // @ts-ignore - Ignoring type checking for environment access
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) ||
    // @ts-ignore - Ignoring type checking for environment access
    (typeof process !== 'undefined' && process.env && process.env[key]) ||
    defaultValue
  );
};

const config: Config = {
  api: {
    baseUrl: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
    path: '/api',
  },
  polling: {
    interval: 3000,
  },
};

export default config;
