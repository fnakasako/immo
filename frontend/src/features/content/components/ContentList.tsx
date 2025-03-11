/**
 * Content List Component
 * Displays a list of content generations and allows creating new content
 */
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useContent } from '../hooks/useContent';
import { GenerationStatus } from '@/types';
import { generatePath, ROUTES } from '@/app/routes';
import './ContentList.css';

const ContentList: React.FC = () => {
  const navigate = useNavigate();
  const { 
    contentList, 
    loading, 
    error, 
    getContentList,
    clearError
  } = useContent();

  useEffect(() => {
    getContentList();
  }, [getContentList]);

  const handleSelectContent = (contentId: string): void => {
    navigate(generatePath.contentView(contentId));
  };

  const handleCreateNew = (): void => {
    navigate(ROUTES.CONTENT_CREATE);
  };

  const getStatusClass = (status: string): string => {
    switch (status) {
      case GenerationStatus.COMPLETED:
        return 'status-complete';
      case GenerationStatus.FAILED:
        return 'status-error';
      case GenerationStatus.PENDING:
        return 'status-pending';
      default:
        return 'status-processing';
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  if (loading) {
    return <div className="loading">Loading content list...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={() => getContentList()}>Retry</button>
        <button onClick={handleCreateNew}>Create New Content</button>
      </div>
    );
  }

  return (
    <div className="content-list">
      <header className="content-list-header">
        <h2>Your Content</h2>
        <button className="new-content-button" onClick={handleCreateNew}>
          Create New Content
        </button>
      </header>

      {contentList.length === 0 ? (
        <div className="no-content">
          <p>You haven't created any content yet.</p>
          <button onClick={handleCreateNew}>Create Your First Content</button>
        </div>
      ) : (
        <div className="content-items">
          {contentList.map((content) => (
            <div
              key={content.id}
              className={`content-item ${getStatusClass(content.status)}`}
              onClick={() => handleSelectContent(content.id)}
            >
              <h3>{content.title || 'Untitled Content'}</h3>
              <div className="content-meta">
                <span className="content-status">{content.status}</span>
                <span className="content-date">Created: {formatDate(content.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentList;
