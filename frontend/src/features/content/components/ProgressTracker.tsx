/**
 * Progress Tracker Component
 * Displays the progress of content generation
 */
import React from 'react';
import { ContentGenerationResponse, GenerationStatus } from '@/types';
import './ProgressTracker.css';

interface ProgressTrackerProps {
  content: ContentGenerationResponse;
  onRetry: () => void;
}

const statusMessages: Record<string, string> = {
  pending: 'Preparing to generate your content...',
  processing_outline: 'Crafting your story outline...',
  processing_sections: 'Creating detailed sections...',
  processing_scenes: 'Developing scenes for your content...',
  processing_prose: 'Writing prose for your scenes...',
  completed: 'Generation complete! Your content is ready.',
  partially_completed: 'Most of your content is ready, with some sections still processing.',
  failed: 'We encountered an issue. Please try again.'
};

const ProgressTracker: React.FC<ProgressTrackerProps> = ({ content, onRetry }) => {
  const { status, progress = 0, error } = content;

  const getStatusText = (): string => {
    return statusMessages[status] || 'Processing...';
  };

  return (
    <div className="progress-tracker">
      <h3>Generation Status</h3>

      <div className="progress-bar-container">
        <div 
          className="progress-bar"
          style={{ width: `${progress}%` }}>
        </div>
        <span className="progress-text">{progress}%</span>
      </div>

      <div className={`status-message ${status}`}>
        <p>{getStatusText()}</p>
        {status === GenerationStatus.FAILED && (
          <div className="error-container">
            <p className="error-message">{error}</p>
            <button className="retry-button" onClick={onRetry}>
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressTracker;
