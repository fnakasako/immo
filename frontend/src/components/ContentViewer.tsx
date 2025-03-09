// src/components/ContentViewer.tsx
import React, { useState, useEffect } from 'react';
import { contentApi } from '../api/contentApi';
import ProgressTracker from './ProgressTracker';
import SectionView from './SectionView';
import { ContentGenerationResponse, SectionResponse, GenerationStatus } from '../../types';
import '../styles/ContentViewer.css';

interface ContentViewerProps {
  contentId: string;
  onReset: () => void;
}

const ContentViewer: React.FC<ContentViewerProps> = ({ contentId, onReset }) => {
  const [content, setContent] = useState<ContentGenerationResponse | null>(null);
  const [sections, setSections] = useState<SectionResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<number>(1);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadContent();
    
    // Start polling for updates
    const interval = setInterval(loadContent, 3000);
    setPollingInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [contentId]);

  useEffect(() => {
    if (content && content.status === GenerationStatus.COMPLETED) {
      loadSections();
      // Stop polling when completed
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  }, [content?.status]);

  const loadContent = async (): Promise<void> => {
    try {
      const contentData = await contentApi.getContent(contentId);
      setContent(contentData);
      setError(null);
      
      if ([
        GenerationStatus.COMPLETED, 
        GenerationStatus.PARTIALLY_COMPLETED, 
        GenerationStatus.FAILED
      ].includes(contentData.status as GenerationStatus)) {
        // Load sections when in final state
        loadSections();
        // Stop polling
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
      }
    } catch (error) {
      console.error('Failed to load content:', error);
      setError('Unable to load content information');
      // Stop polling on error
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadSections = async (): Promise<void> => {
    try {
      const sectionsData = await contentApi.getSections(contentId);
      setSections(sectionsData.sections);
    } catch (error) {
      console.error('Failed to load sections:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading content...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={onReset}>Create New Content</button>
      </div>
    );
  }

  return (
    <div className="content-viewer">
      <header className="content-header">
        <h2>{content?.title || 'Generating Content...'}</h2>
        <button className="new-content-button" onClick={onReset}>
          Create New Content
        </button>
      </header>
      
      {content && (
        <ProgressTracker 
          content={content} 
          onRetry={onReset} 
        />
      )}
      
      {content?.outline && (
        <div className="content-outline">
          <h3>Content Overview</h3>
          <p>{content.outline}</p>
        </div>
      )}
      
      {sections.length > 0 && (
        <div className="sections-container">
          <h3>Sections</h3>
          {sections.map(section => (
            <SectionView
              key={section.number}
              contentId={contentId}
              section={section}
              isActive={section.number === activeSection}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentViewer;
