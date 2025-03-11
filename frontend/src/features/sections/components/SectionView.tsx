/**
 * Section View Component
 * Displays and manages a single section and its scenes
 */
import React, { useState, useEffect } from 'react';
import { useSections } from '../hooks/useSections';
import { useScenes } from '@/features/scenes/hooks/useScenes';
import SceneView from '@/features/scenes/components/SceneView';
import { 
  SectionResponse, 
  SectionStatus,
  SectionUpdateRequest
} from '@/types';
import './SectionView.css';

interface SectionViewProps {
  contentId: string;
  section: SectionResponse;
  isActive: boolean;
}

const SectionView: React.FC<SectionViewProps> = ({ contentId, section, isActive }) => {
  const { updateSection } = useSections();
  const { scenes, setScenes, generateProse, loading: scenesLoading, error: scenesError } = useScenes();
  
  const [expanded, setExpanded] = useState<boolean>(isActive);
  const [activeScene, setActiveScene] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // State for editing section
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedTitle, setEditedTitle] = useState<string>('');
  const [editedSummary, setEditedSummary] = useState<string>('');
  
  // State for scene selection
  const [selectedScenes, setSelectedScenes] = useState<number[]>([]);

  useEffect(() => {
    if (expanded && scenes.length === 0) {
      loadScenes();
    }
  }, [expanded]);

  useEffect(() => {
    setExpanded(isActive);
  }, [isActive]);
  
  useEffect(() => {
    // Initialize editing state with current values
    if (section) {
      setEditedTitle(section.title);
      setEditedSummary(section.summary || '');
    }
  }, [section]);

  const loadScenes = async (): Promise<void> => {
    if (!contentId || !section) return;
    
    setLoading(true);
    try {
      // This will be handled by the scenes slice
      // For now, we'll just set a placeholder
      setLoading(false);
    } catch (error) {
      console.error('Failed to load scenes:', error);
      setError('Failed to load scenes');
      setLoading(false);
    }
  };
  
  // Save edited section
  const handleSaveSection = async (): Promise<void> => {
    setLoading(true);
    try {
      const updateData: SectionUpdateRequest = {
        title: editedTitle,
        summary: editedSummary
      };
      await updateSection(contentId, section.number, updateData);
      setIsEditing(false);
      setError(null);
    } catch (error) {
      console.error('Failed to update section:', error);
      setError('Failed to update section');
    } finally {
      setLoading(false);
    }
  };
  
  // Toggle scene selection
  const toggleSceneSelection = (sceneNumber: number): void => {
    setSelectedScenes(prev => {
      if (prev.includes(sceneNumber)) {
        return prev.filter(num => num !== sceneNumber);
      } else {
        return [...prev, sceneNumber];
      }
    });
  };
  
  // Generate prose for selected scenes
  const handleGenerateProse = async (): Promise<void> => {
    if (selectedScenes.length === 0) {
      setError('Please select at least one scene');
      return;
    }
    
    try {
      await generateProse(contentId, section.number, selectedScenes);
      setSelectedScenes([]);
      setError(null);
    } catch (error) {
      console.error('Failed to generate prose:', error);
      setError('Failed to generate prose');
    }
  };

  const toggleExpand = (): void => {
    setExpanded(!expanded);
  };

  const getStatusClass = (): string => {
    switch (section.status) {
      case 'completed': return 'status-complete';
      case 'failed': return 'status-error';
      case 'pending': return 'status-pending';
      default: return 'status-processing';
    }
  };

  return (
    <div className={`section-view ${expanded ? 'expanded' : 'collapsed'}`}>
      <div className="section-header">
        <div className="section-title" onClick={toggleExpand}>
          <span className={`status-indicator ${getStatusClass()}`} />
          <h3>Section {section.number}: {section.title}</h3>
        </div>
        <div className="section-controls">
          {!isEditing && (
            <button 
              className="edit-button"
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
              }}
            >
              Edit
            </button>
          )}
          <button 
            className="expand-button"
            onClick={toggleExpand}
          >
            {expanded ? '▼' : '►'}
          </button>
        </div>
      </div>
      
      {expanded && (
        <div className="section-content">
          {isEditing ? (
            <div className="section-editor">
              <div className="form-group">
                <label htmlFor={`section-title-${section.number}`}>Title</label>
                <input
                  type="text"
                  id={`section-title-${section.number}`}
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  placeholder="Enter section title"
                />
              </div>
              <div className="form-group">
                <label htmlFor={`section-summary-${section.number}`}>Summary</label>
                <textarea
                  id={`section-summary-${section.number}`}
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  placeholder="Enter section summary"
                  rows={4}
                />
              </div>
              <div className="editor-actions">
                <button 
                  className="save-button"
                  onClick={handleSaveSection}
                  disabled={loading}
                >
                  Save
                </button>
                <button 
                  className="cancel-button"
                  onClick={() => {
                    setIsEditing(false);
                    setEditedTitle(section.title);
                    setEditedSummary(section.summary || '');
                  }}
                >
                  Cancel
                </button>
              </div>
              {error && <div className="error-message">{error}</div>}
            </div>
          ) : (
            <div className="section-summary">
              <h4>Summary</h4>
              <p>{section.summary}</p>
            </div>
          )}
          
          {loading || scenesLoading ? (
            <div className="loading">Loading scenes...</div>
          ) : (
            <>
              {/* Scene Generation Controls */}
              {section.status === SectionStatus.SCENES_COMPLETED && scenes.length > 0 && (
                <div className="prose-generation-controls">
                  <div className="scene-selection">
                    <h4>Select scenes for prose generation:</h4>
                    <div className="scene-checkboxes">
                      {scenes.map(scene => (
                        <label key={scene.number} className="scene-checkbox-label">
                          <input
                            type="checkbox"
                            checked={selectedScenes.includes(scene.number)}
                            onChange={() => toggleSceneSelection(scene.number)}
                          />
                          Scene {scene.number}
                        </label>
                      ))}
                    </div>
                  </div>
                  <button 
                    className="generate-button"
                    onClick={handleGenerateProse}
                    disabled={loading || selectedScenes.length === 0}
                  >
                    Generate Prose for Selected Scenes
                  </button>
                  {error && <div className="error-message">{error}</div>}
                  {scenesError && <div className="error-message">{scenesError}</div>}
                </div>
              )}
              
              <div className="scene-tabs">
                {scenes.map(scene => (
                  <button
                    key={scene.number}
                    className={`scene-tab ${scene.number === activeScene ? 'active' : ''}`}
                    onClick={() => setActiveScene(scene.number)}
                  >
                    Scene {scene.number}
                  </button>
                ))}
              </div>
              
              {activeScene && (
                <SceneView
                  contentId={contentId}
                  sectionNumber={section.number}
                  sceneNumber={activeScene}
                />
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SectionView;
