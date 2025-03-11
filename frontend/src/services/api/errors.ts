/**
 * API Error Classes
 * 
 * Custom error classes for the API client to provide more detailed error information
 * and better recovery options.
 */

/**
 * Base API Error class
 * Represents an error returned by the API
 */
export class ApiError extends Error {
  status: number;
  data: any;
  
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    
    // This is needed to make instanceof work correctly with custom Error classes
    Object.setPrototypeOf(this, ApiError.prototype);
  }
  
  /**
   * Check if the error is a client error (4xx)
   */
  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }
  
  /**
   * Check if the error is a server error (5xx)
   */
  isServerError(): boolean {
    return this.status >= 500 && this.status < 600;
  }
  
  /**
   * Check if the error is an authentication error (401)
   */
  isAuthError(): boolean {
    return this.status === 401;
  }
  
  /**
   * Check if the error is a forbidden error (403)
   */
  isForbiddenError(): boolean {
    return this.status === 403;
  }
  
  /**
   * Check if the error is a not found error (404)
   */
  isNotFoundError(): boolean {
    return this.status === 404;
  }
}

/**
 * Network Error class
 * Represents a network error (e.g. connection refused, timeout)
 */
export class NetworkError extends Error {
  constructor(message: string = 'Network error occurred') {
    super(message);
    this.name = 'NetworkError';
    
    // This is needed to make instanceof work correctly with custom Error classes
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

/**
 * Timeout Error class
 * Represents a request timeout
 */
export class TimeoutError extends Error {
  constructor(message: string = 'Request timed out') {
    super(message);
    this.name = 'TimeoutError';
    
    // This is needed to make instanceof work correctly with custom Error classes
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

/**
 * Parse Error class
 * Represents an error parsing the response
 */
export class ParseError extends Error {
  constructor(message: string = 'Failed to parse response') {
    super(message);
    this.name = 'ParseError';
    
    // This is needed to make instanceof work correctly with custom Error classes
    Object.setPrototypeOf(this, ParseError.prototype);
  }
}

/**
 * Abort Error class
 * Represents a request that was aborted
 */
export class AbortError extends Error {
  constructor(message: string = 'Request was aborted') {
    super(message);
    this.name = 'AbortError';
    
    // This is needed to make instanceof work correctly with custom Error classes
    Object.setPrototypeOf(this, AbortError.prototype);
  }
}

/**
 * Get a user-friendly error message based on the error
 */
export function getUserFriendlyErrorMessage(error: Error): string {
  if (error instanceof ApiError) {
    if (error.isAuthError()) {
      return 'You are not authenticated. Please log in and try again.';
    } else if (error.isForbiddenError()) {
      return 'You do not have permission to perform this action.';
    } else if (error.isNotFoundError()) {
      return 'The requested resource was not found.';
    } else if (error.isClientError()) {
      return error.message || 'There was an error with your request.';
    } else if (error.isServerError()) {
      return 'The server encountered an error. Please try again later.';
    }
  } else if (error instanceof NetworkError) {
    return 'Unable to connect to the server. Please check your internet connection.';
  } else if (error instanceof TimeoutError) {
    return 'The request took too long to complete. Please try again.';
  } else if (error instanceof ParseError) {
    return 'There was an error processing the response from the server.';
  } else if (error instanceof AbortError) {
    return 'The request was cancelled.';
  }
  
  return error.message || 'An unexpected error occurred.';
}
