/**
 * Content Error Boundary Component
 * 
 * A specialized error boundary for content-related components
 * with a custom fallback UI specific to content errors.
 */
import React from 'react';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import './ContentErrorBoundary.css';

interface ContentErrorBoundaryProps {
  children: React.ReactNode;
}

const ContentErrorFallback: React.FC = () => (
  <div className="content-error-fallback">
    <h3>Error Loading Content</h3>
    <p>We encountered an issue while loading or processing your content.</p>
    <p>This could be due to:</p>
    <ul>
      <li>A temporary server issue</li>
      <li>Network connectivity problems</li>
      <li>An issue with the content data</li>
    </ul>
    <p>Please try again later or contact support if the problem persists.</p>
  </div>
);

const ContentErrorBoundary: React.FC<ContentErrorBoundaryProps> = ({ children }) => {
  const handleError = (error: Error): void => {
    // In a production app, you would log this to a monitoring service
    console.error('Content component error:', error);
    
    // You could also send this to an analytics service
    // analytics.trackError('content_component_error', { message: error.message });
  };

  return (
    <ErrorBoundary 
      fallback={<ContentErrorFallback />}
      onError={handleError}
    >
      {children}
    </ErrorBoundary>
  );
};

export default ContentErrorBoundary;
