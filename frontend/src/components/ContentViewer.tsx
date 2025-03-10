// src/components/ContentViewer.tsx
import React, { useState, useEffect } from 'react';
import { contentApi } from '../api/contentApi';
import ProgressTracker from './ProgressTracker';
import SectionView from './SectionView';
import { 
  ContentGenerationResponse, 
  SectionResponse, 
  GenerationStatus,
  ContentUpdateRequest
} from '../../types';
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

  // State for editing outline
  const [isEditingOutline, setIsEditingOutline] = useState<boolean>(false);
  const [editedTitle, setEditedTitle] = useState<string>('');
  const [editedOutline, setEditedOutline] = useState<string>('');
  // State for section selection
  const [selectedSections, setSelectedSections] = useState<number[]>([]);

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
    if (content) {
      // Initialize editing state with current values
      setEditedTitle(content.title || '');
      setEditedOutline(content.outline || '');
      
      // Load sections for various states
      if ([
        GenerationStatus.OUTLINE_COMPLETED,
        GenerationStatus.SECTIONS_COMPLETED,
        GenerationStatus.SCENES_COMPLETED,
        GenerationStatus.PROCESSING_PROSE,
        GenerationStatus.COMPLETED, 
        GenerationStatus.PARTIALLY_COMPLETED, 
        GenerationStatus.FAILED
      ].includes(content.status as GenerationStatus)) {
        loadSections();
      }
      
      // Stop polling when in a final state
      if ([
        GenerationStatus.COMPLETED, 
        GenerationStatus.PARTIALLY_COMPLETED, 
        GenerationStatus.FAILED
      ].includes(content.status as GenerationStatus)) {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
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
  
  // Generate outline
  const handleGenerateOutline = async (): Promise<void> => {
    setLoading(true);
    try {
      await contentApi.generateOutline(contentId);
      await loadContent();
    } catch (error) {
      console.error('Failed to generate outline:', error);
      setError('Failed to generate outline');
    } finally {
      setLoading(false);
    }
  };
  
  // Save edited outline
  const handleSaveOutline = async (): Promise<void> => {
    setLoading(true);
    try {
      const updateData: ContentUpdateRequest = {
        title: editedTitle,
        outline: editedOutline
      };
      await contentApi.updateOutline(contentId, updateData);
      await loadContent();
      setIsEditingOutline(false);
    } catch (error) {
      console.error('Failed to update outline:', error);
      setError('Failed to update outline');
    } finally {
      setLoading(false);
    }
  };
  
  // Generate sections
  const handleGenerateSections = async (): Promise<void> => {
    setLoading(true);
    try {
      await contentApi.generateSections(contentId);
      await loadContent();
      await loadSections();
    } catch (error) {
      console.error('Failed to generate sections:', error);
      setError('Failed to generate sections');
    } finally {
      setLoading(false);
    }
  };
  
  // Toggle section selection
  const toggleSectionSelection = (sectionNumber: number): void => {
    setSelectedSections(prev => {
      if (prev.includes(sectionNumber)) {
        return prev.filter(num => num !== sectionNumber);
      } else {
        return [...prev, sectionNumber];
      }
    });
  };
  
  // Generate scenes for selected sections
  const handleGenerateScenes = async (): Promise<void> => {
    if (selectedSections.length === 0) {
      setError('Please select at least one section');
      return;
    }
    
    setLoading(true);
    try {
      await contentApi.generateScenes(contentId, selectedSections);
      await loadContent();
      await loadSections();
      setSelectedSections([]);
    } catch (error) {
      console.error('Failed to generate scenes:', error);
      setError('Failed to generate scenes');
    } finally {
      setLoading(false);
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
      
      {/* Outline Section */}
      <div className="content-outline-section">
        <div className="section-header">
          <h3>Content Overview</h3>
          <div className="section-actions">
            {content?.status === GenerationStatus.PENDING && (
              <button 
                className="action-button"
                onClick={handleGenerateOutline}
                disabled={loading}
              >
                Generate Outline
              </button>
            )}
            
            {content?.outline && !isEditingOutline && (
              <button 
                className="edit-button"
                onClick={() => setIsEditingOutline(true)}
              >
                Edit
              </button>
            )}
            
            {isEditingOutline && (
              <>
                <button 
                  className="save-button"
                  onClick={handleSaveOutline}
                  disabled={loading}
                >
                  Save
                </button>
                <button 
                  className="cancel-button"
                  onClick={() => {
                    setIsEditingOutline(false);
                    setEditedTitle(content?.title || '');
                    setEditedOutline(content?.outline || '');
                  }}
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
        
        {isEditingOutline ? (
          <div className="outline-editor">
            <div className="form-group">
              <label htmlFor="title">Title</label>
              <input
                type="text"
                id="title"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                placeholder="Enter title"
              />
            </div>
            <div className="form-group">
              <label htmlFor="outline">Outline</label>
              <textarea
                id="outline"
                value={editedOutline}
                onChange={(e) => setEditedOutline(e.target.value)}
                placeholder="Enter outline"
                rows={5}
              />
            </div>
          </div>
        ) : (
          content?.outline && (
            <div className="content-outline">
              <h3>{content.title}</h3>
              <p>{content.outline}</p>
            </div>
          )
        )}
      </div>
      
      {/* Sections Generation Button */}
      {content?.status === GenerationStatus.OUTLINE_COMPLETED && (
        <div className="generation-controls">
          <button 
            className="generate-button"
            onClick={handleGenerateSections}
            disabled={loading}
          >
            Generate Sections
          </button>
        </div>
      )}
      
      {/* Sections List */}
      {sections.length > 0 && (
        <div className="sections-container">
          <div className="sections-header">
            <h3>Sections</h3>
            
            {/* Scene Generation Controls */}
            {content?.status === GenerationStatus.SECTIONS_COMPLETED && (
              <div className="scene-generation-controls">
                <button 
                  className="generate-button"
                  onClick={handleGenerateScenes}
                  disabled={loading || selectedSections.length === 0}
                >
                  Generate Scenes for Selected Sections
                </button>
              </div>
            )}
          </div>
          
          {sections.map(section => (
            <div key={section.number} className="section-item-container">
              {content?.status === GenerationStatus.SECTIONS_COMPLETED && (
                <div className="section-checkbox">
                  <input
                    type="checkbox"
                    id={`section-${section.number}`}
                    checked={selectedSections.includes(section.number)}
                    onChange={() => toggleSectionSelection(section.number)}
                  />
                </div>
              )}
              <div className="section-view-container">
                <SectionView
                  key={section.number}
                  contentId={contentId}
                  section={section}
                  isActive={section.number === activeSection}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentViewer;
