// src/components/ContentList.tsx
import React, { useState, useEffect } from 'react';
import { contentApi } from '../api/contentApi';
import { ContentGenerationResponse, GenerationStatus } from '../../types';
import '../styles/ContentList.css';

interface ContentListProps {
  onSelectContent: (contentId: string) => void;
  onCreateNew: () => void;
}

const ContentList: React.FC<ContentListProps> = ({ onSelectContent, onCreateNew }) => {
  const [contentList, setContentList] = useState<ContentGenerationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadContentList();
  }, []);

  const loadContentList = async (): Promise<void> => {
    setLoading(true);
    try {
      const list = await contentApi.listContent();
      setContentList(list);
      setError(null);
    } catch (error) {
      console.error('Failed to load content list:', error);
      setError('Unable to load content list');
    } finally {
      setLoading(false);
    }
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
        <button onClick={loadContentList}>Retry</button>
        <button onClick={onCreateNew}>Create New Content</button>
      </div>
    );
  }

  return (
    <div className="content-list">
      <header className="content-list-header">
        <h2>Your Content</h2>
        <button className="new-content-button" onClick={onCreateNew}>
          Create New Content
        </button>
      </header>

      {contentList.length === 0 ? (
        <div className="no-content">
          <p>You haven't created any content yet.</p>
          <button onClick={onCreateNew}>Create Your First Content</button>
        </div>
      ) : (
        <div className="content-items">
          {contentList.map((content) => (
            <div
              key={content.id}
              className={`content-item ${getStatusClass(content.status)}`}
              onClick={() => onSelectContent(content.id)}
            >
              <h3>{content.title || 'Untitled Content'}</h3>
              <p className="content-description">{content.description}</p>
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
