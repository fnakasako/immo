/**
 * Content Viewer Component
 * Displays and manages content generation
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useContent } from '../hooks/useContent';
import { useSections } from '@/features/sections/hooks/useSections';
import ProgressTracker from './ProgressTracker';
import SectionView from '@/features/sections/components/SectionView';
import { 
  ContentUpdateRequest,
  GenerationStatus
} from '@/types';
import { ROUTES } from '@/app/routes';
import './ContentViewer.css';

const ContentViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const { 
    currentContent: content, 
    loading: contentLoading, 
    error: contentError,
    getContentById,
    generateOutline,
    updateOutline,
    generateSections,
    generateScenes,
    clearError
  } = useContent();
  
  const {
    sections,
    getSections
  } = useSections();
  
  const [activeSection, setActiveSection] = useState<number>(1);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // State for editing outline
  const [isEditingOutline, setIsEditingOutline] = useState<boolean>(false);
  const [editedTitle, setEditedTitle] = useState<string>('');
  const [editedOutline, setEditedOutline] = useState<string>('');
  
  // State for section selection
  const [selectedSections, setSelectedSections] = useState<number[]>([]);

  // Load content on mount
  useEffect(() => {
    if (id) {
      getContentById(id);
      
      // Start polling for updates
      const interval = setInterval(() => {
        if (id) getContentById(id);
      }, 3000);
      
      setPollingInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [id, getContentById]);

  // Handle content status changes
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
      ].includes(content.status as GenerationStatus) && id) {
        getSections(id);
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
  }, [content?.status, id, getSections, pollingInterval]);

  const handleCreateNew = () => {
    navigate(ROUTES.CONTENT_CREATE);
  };
  
  // Generate outline
  const handleGenerateOutline = async () => {
    if (id) {
      await generateOutline(id);
    }
  };
  
  // Save edited outline
  const handleSaveOutline = async () => {
    if (id) {
      const updateData: ContentUpdateRequest = {
        title: editedTitle,
        outline: editedOutline
      };
      await updateOutline(id, updateData);
      setIsEditingOutline(false);
    }
  };
  
  // Generate sections
  const handleGenerateSections = async () => {
    if (id) {
      await generateSections(id);
    }
  };
  
  // Toggle section selection
  const toggleSectionSelection = (sectionNumber: number) => {
    setSelectedSections(prev => {
      if (prev.includes(sectionNumber)) {
        return prev.filter(num => num !== sectionNumber);
      } else {
        return [...prev, sectionNumber];
      }
    });
  };
  
  // Generate scenes for selected sections
  const handleGenerateScenes = async () => {
    if (selectedSections.length === 0) {
      // Show error message
      return;
    }
    
    if (id) {
      await generateScenes(id, selectedSections);
      setSelectedSections([]);
    }
  };

  if (contentLoading) {
    return <div className="loading">Loading content...</div>;
  }

  if (contentError) {
    return (
      <div className="error-container">
        <h3>Error</h3>
        <p>{contentError}</p>
        <button onClick={handleCreateNew}>Create New Content</button>
      </div>
    );
  }

  if (!content) {
    return <div className="loading">Content not found</div>;
  }

  return (
    <div className="content-viewer">
      <header className="content-header">
        <h2>{content.title || 'Generating Content...'}</h2>
        <button className="new-content-button" onClick={handleCreateNew}>
          Create New Content
        </button>
      </header>
      
      <ProgressTracker 
        content={content} 
        onRetry={handleCreateNew} 
      />
      
      {/* Outline Section */}
      <div className="content-outline-section">
        <div className="section-header">
          <h3>Content Overview</h3>
          <div className="section-actions">
            {content.status === GenerationStatus.PENDING && (
              <button 
                className="action-button"
                onClick={handleGenerateOutline}
                disabled={contentLoading}
              >
                Generate Outline
              </button>
            )}
            
            {content.outline && !isEditingOutline && (
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
                  disabled={contentLoading}
                >
                  Save
                </button>
                <button 
                  className="cancel-button"
                  onClick={() => {
                    setIsEditingOutline(false);
                    setEditedTitle(content.title || '');
                    setEditedOutline(content.outline || '');
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
          content.outline && (
            <div className="content-outline">
              <h3>{content.title}</h3>
              <p>{content.outline}</p>
            </div>
          )
        )}
      </div>
      
      {/* Sections Generation Button */}
      {content.status === GenerationStatus.OUTLINE_COMPLETED && (
        <div className="generation-controls">
          <button 
            className="generate-button"
            onClick={handleGenerateSections}
            disabled={contentLoading}
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
            {content.status === GenerationStatus.SECTIONS_COMPLETED && (
              <div className="scene-generation-controls">
                <button 
                  className="generate-button"
                  onClick={handleGenerateScenes}
                  disabled={contentLoading || selectedSections.length === 0}
                >
                  Generate Scenes for Selected Sections
                </button>
              </div>
            )}
          </div>
          
          {sections.map(section => (
            <div key={section.number} className="section-item-container">
              {content.status === GenerationStatus.SECTIONS_COMPLETED && (
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
                {id && (
                  <SectionView
                    contentId={id}
                    section={section}
                    isActive={section.number === activeSection}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentViewer;
