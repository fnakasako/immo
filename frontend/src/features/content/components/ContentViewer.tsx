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
  SectionResponse
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
    }
  }, [id, getContentById]);
  
  // Setup polling for content updates
  useEffect(() => {
    // Only start polling if content exists and is not in a final state
    const statusStr = String(content?.status || '');
    if (id && content && 
        !statusStr.includes('COMPLETED') && 
        !statusStr.includes('completed') && 
        !statusStr.includes('FAILED') && 
        !statusStr.includes('failed')) {
      // Clear any existing interval first
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
      
      // Start a new polling interval
      const interval = setInterval(() => {
        getContentById(id);
      }, 3000);
      
      setPollingInterval(interval);
      
      // Clean up on unmount or when dependencies change
      return () => {
        clearInterval(interval);
        setPollingInterval(null);
      };
    } else if (pollingInterval && content) {
      const statusStr = String(content.status || '');
      if (statusStr.includes('COMPLETED') || 
          statusStr.includes('completed') || 
          statusStr.includes('FAILED') || 
          statusStr.includes('failed')) {
        // If we have a polling interval but content is in a final state, clear it
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  }, [id, content, pollingInterval, getContentById]);

  // Handle content status changes
  useEffect(() => {
    if (content) {
      // Initialize editing state with current values
      setEditedTitle(content.title || '');
      setEditedOutline(content.outline || '');
      
      // Load sections for various states
      const statusStr = String(content.status || '');
      if ((statusStr.includes('OUTLINE_COMPLETED') || 
           statusStr.includes('outline_completed') ||
           statusStr.includes('SECTIONS_COMPLETED') || 
           statusStr.includes('sections_completed') ||
           statusStr.includes('SCENES_COMPLETED') || 
           statusStr.includes('scenes_completed') ||
           statusStr.includes('PROCESSING_PROSE') || 
           statusStr.includes('processing_prose') ||
           statusStr.includes('COMPLETED') || 
           statusStr.includes('completed') ||
           statusStr.includes('FAILED') || 
           statusStr.includes('failed')) && id) {
        getSections(id);
      }
      
      // Stop polling when in a final state
      if (statusStr.includes('COMPLETED') || 
          statusStr.includes('completed') || 
          statusStr.includes('FAILED') || 
          statusStr.includes('failed')) {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
      }
    }
  }, [content?.status, id, getSections, pollingInterval]);
  
  // Stop polling when an error occurs
  useEffect(() => {
    if (contentError && pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  }, [contentError, pollingInterval]);

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
        {contentError.includes('Authentication failed') ? (
          <button onClick={() => window.location.href = '/login'}>Log In Again</button>
        ) : (
          <button onClick={handleCreateNew}>Create New Content</button>
        )}
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
      
      
      {/* Outline Section */}
      <div className="content-outline-section">
        <div className="section-header">
          <h3>Content Overview</h3>
          <div className="section-actions">
            {(String(content.status).includes("PENDING") || 
              String(content.status).includes("pending")) && (
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
      {(String(content.status).includes("OUTLINE_COMPLETED") || 
        String(content.status).includes("outline_completed")) && (
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
            {(String(content.status).includes("SECTIONS_COMPLETED") || 
              String(content.status).includes("sections_completed")) && (
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
          
          {sections.map((section: SectionResponse) => (
            <div key={section.number} className="section-item-container">
              {(String(content.status).includes("SECTIONS_COMPLETED") || 
                String(content.status).includes("sections_completed")) && (
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
