/**
 * API Client
 * Provides a centralized client for making API requests with consistent error handling
 * and retry logic for transient errors.
 */
import axios from 'axios';
import config from '@/app/config';
import { 
  ApiError, 
  NetworkError, 
  TimeoutError, 
  ParseError, 
  AbortError 
} from './errors';

// Type definitions for axios
interface AxiosResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: any;
}

interface AxiosError {
  response?: {
    status: number;
    data: any;
  };
  code?: string;
  message: string;
}

// Base URL for API requests
const BASE_URL = `${config.api.baseUrl}${config.api.path}`;

// Default request timeout in milliseconds
const DEFAULT_TIMEOUT = 30000; // 30 seconds

// Default number of retries for transient errors
const DEFAULT_RETRIES = 3;

// Default delay between retries in milliseconds
const DEFAULT_RETRY_DELAY = 300; // 300ms, doubles each retry

/**
 * Enhanced error handling function that converts Axios errors to our custom error types
 */
const handleApiError = (error: any): never => {
  // Handle Axios errors
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    
    // Handle network errors
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        throw new TimeoutError();
      }
      
      if (axiosError.message.includes('Network Error')) {
        throw new NetworkError();
      }
      
      throw new NetworkError(axiosError.message);
    }
    
    // Handle API errors with response
    const status = axiosError.response.status;
    let errorData;
    
    try {
      errorData = axiosError.response.data;
    } catch (e) {
      errorData = { message: 'Unknown error' };
    }
    
    const errorMessage = errorData.detail || errorData.message || axiosError.message || 'Unknown error occurred';
    
    throw new ApiError(errorMessage, status, errorData);
  }
  
  // Handle abort errors
  if (error.name === 'AbortError' || error.name === 'CanceledError') {
    throw new AbortError();
  }
  
  // Handle parse errors
  if (error instanceof SyntaxError && error.message.includes('JSON')) {
    throw new ParseError();
  }
  
  // Handle other errors
  throw error;
};

/**
 * Fetch with retry logic for transient errors
 */
const fetchWithRetry = async <T>(
  requestFn: () => Promise<AxiosResponse<T>>,
  retries = DEFAULT_RETRIES,
  delay = DEFAULT_RETRY_DELAY
): Promise<AxiosResponse<T>> => {
  try {
    return await requestFn();
  } catch (error) {
    // Don't retry if we're out of retries or it's not a network error
    if (retries <= 0 || !(error instanceof NetworkError || error instanceof TimeoutError)) {
      throw error;
    }
    
    // Wait before retrying
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // Retry with exponential backoff
    return fetchWithRetry(requestFn, retries - 1, delay * 2);
  }
};

// Generic request methods with error handling
export const apiRequest = {
  get: async <T>(url: string, config?: any): Promise<T> => {
    try {
      const response = await axios.get(`${BASE_URL}${url}`, {
        headers: { 'Content-Type': 'application/json' },
        ...config
      });
      return response.data;
    } catch (error) {
      return handleApiError(error) as Promise<T>;
    }
  },
  
  post: async <T>(url: string, data?: any, config?: any): Promise<T> => {
    try {
      const response = await axios.post(`${BASE_URL}${url}`, data, {
        headers: { 'Content-Type': 'application/json' },
        ...config
      });
      return response.data;
    } catch (error) {
      return handleApiError(error) as Promise<T>;
    }
  },
  
  put: async <T>(url: string, data?: any, config?: any): Promise<T> => {
    try {
      const response = await axios.put(`${BASE_URL}${url}`, data, {
        headers: { 'Content-Type': 'application/json' },
        ...config
      });
      return response.data;
    } catch (error) {
      return handleApiError(error) as Promise<T>;
    }
  },
  
  delete: async <T>(url: string, config?: any): Promise<T> => {
    try {
      const response = await axios.delete(`${BASE_URL}${url}`, {
        headers: { 'Content-Type': 'application/json' },
        ...config
      });
      return response.data;
    } catch (error) {
      return handleApiError(error) as Promise<T>;
    }
  }
};

// Export the API request object as default
export default apiRequest;
