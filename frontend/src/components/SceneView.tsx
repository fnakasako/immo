// src/components/SceneView.tsx
import React, { useState, useEffect } from 'react';
import { contentApi } from '../api/contentApi';
import { SceneResponse, SceneStatus, SceneUpdateRequest } from '../../types';
import '../styles/SceneView.css';

interface SceneViewProps {
  contentId: string;
  sectionNumber: number;
  sceneNumber: number;
}

type ViewMode = 'prose' | 'metadata';

const SceneView: React.FC<SceneViewProps> = ({ contentId, sectionNumber, sceneNumber }) => {
  const [scene, setScene] = useState<SceneResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('prose');
  
  // State for editing scene
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedHeading, setEditedHeading] = useState<string>('');
  const [editedSetting, setEditedSetting] = useState<string>('');
  const [editedCharacters, setEditedCharacters] = useState<string>('');
  const [editedKeyEvents, setEditedKeyEvents] = useState<string>('');
  const [editedEmotionalTone, setEditedEmotionalTone] = useState<string>('');
  const [editedContent, setEditedContent] = useState<string>('');

  useEffect(() => {
    loadScene();
  }, [contentId, sectionNumber, sceneNumber]);
  
  useEffect(() => {
    // Initialize editing state with current values
    if (scene) {
      setEditedHeading(scene.heading || '');
      setEditedSetting(scene.setting || '');
      setEditedCharacters(scene.characters || '');
      setEditedKeyEvents(scene.key_events || '');
      setEditedEmotionalTone(scene.emotional_tone || '');
      setEditedContent(scene.content || '');
    }
  }, [scene]);

  const loadScene = async (): Promise<void> => {
    setLoading(true);
    try {
      const sceneData = await contentApi.getScene(contentId, sectionNumber, sceneNumber);
      setScene(sceneData);
      setError(null);
    } catch (error) {
      console.error('Failed to load scene:', error);
      setError('Unable to load scene content');
    } finally {
      setLoading(false);
    }
  };
  
  // Save edited scene
  const handleSaveScene = async (): Promise<void> => {
    setLoading(true);
    try {
      const updateData: SceneUpdateRequest = {
        heading: editedHeading,
        setting: editedSetting,
        characters: editedCharacters.split(',').map(c => c.trim()),
        key_events: editedKeyEvents,
        emotional_tone: editedEmotionalTone,
        content: editedContent
      };
      await contentApi.updateScene(contentId, sectionNumber, sceneNumber, updateData);
      await loadScene();
      setIsEditing(false);
      setError(null);
    } catch (error) {
      console.error('Failed to update scene:', error);
      setError('Failed to update scene');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="scene-loading">Loading scene...</div>;
  }

  if (error || !scene) {
    return <div className="scene-error">{error || 'Scene not found'}</div>;
  }

  return (
    <div className="scene-view">
      <div className="scene-controls">
        <div className="view-toggles">
          <button 
            className={`view-toggle ${viewMode === 'prose' ? 'active' : ''}`}
            onClick={() => setViewMode('prose')}
          >
            Prose
          </button>
          <button 
            className={`view-toggle ${viewMode === 'metadata' ? 'active' : ''}`}
            onClick={() => setViewMode('metadata')}
          >
            Scene Details
          </button>
        </div>
        
        <div className="action-buttons">
          {!isEditing ? (
            <button 
              className="edit-button"
              onClick={() => setIsEditing(true)}
            >
              Edit Scene
            </button>
          ) : (
            <>
              <button 
                className="save-button"
                onClick={handleSaveScene}
                disabled={loading}
              >
                Save
              </button>
              <button 
                className="cancel-button"
                onClick={() => {
                  setIsEditing(false);
                  // Reset edited values
                  if (scene) {
                    setEditedHeading(scene.heading || '');
                    setEditedSetting(scene.setting || '');
                    setEditedCharacters(scene.characters || '');
                    setEditedKeyEvents(scene.key_events || '');
                    setEditedEmotionalTone(scene.emotional_tone || '');
                    setEditedContent(scene.content || '');
                  }
                }}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
      
      {isEditing ? (
        <div className="scene-editor">
          {viewMode === 'prose' ? (
            <div className="prose-editor">
              <div className="form-group">
                <label htmlFor="scene-content">Prose Content</label>
                <textarea
                  id="scene-content"
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  placeholder="Enter scene prose content"
                  rows={10}
                />
              </div>
            </div>
          ) : (
            <div className="metadata-editor">
              <div className="form-group">
                <label htmlFor="scene-heading">Scene Heading</label>
                <input
                  type="text"
                  id="scene-heading"
                  value={editedHeading}
                  onChange={(e) => setEditedHeading(e.target.value)}
                  placeholder="Enter scene heading"
                />
              </div>
              <div className="form-group">
                <label htmlFor="scene-setting">Setting</label>
                <input
                  type="text"
                  id="scene-setting"
                  value={editedSetting}
                  onChange={(e) => setEditedSetting(e.target.value)}
                  placeholder="Enter scene setting"
                />
              </div>
              <div className="form-group">
                <label htmlFor="scene-characters">Characters (comma-separated)</label>
                <input
                  type="text"
                  id="scene-characters"
                  value={editedCharacters}
                  onChange={(e) => setEditedCharacters(e.target.value)}
                  placeholder="Enter characters, separated by commas"
                />
              </div>
              <div className="form-group">
                <label htmlFor="scene-key-events">Key Events</label>
                <textarea
                  id="scene-key-events"
                  value={editedKeyEvents}
                  onChange={(e) => setEditedKeyEvents(e.target.value)}
                  placeholder="Enter key events"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label htmlFor="scene-emotional-tone">Emotional Tone</label>
                <input
                  type="text"
                  id="scene-emotional-tone"
                  value={editedEmotionalTone}
                  onChange={(e) => setEditedEmotionalTone(e.target.value)}
                  placeholder="Enter emotional tone"
                />
              </div>
            </div>
          )}
          {error && <div className="error-message">{error}</div>}
        </div>
      ) : (
        viewMode === 'prose' ? (
          <div className="scene-prose">
            {scene.status === SceneStatus.COMPLETED ? (
              <div className="prose-content">
                {scene.content && scene.content.split('\n').map((paragraph, i) => (
                  paragraph.trim() && <p key={i}>{paragraph}</p>
                ))}
              </div>
            ) : scene.status === SceneStatus.GENERATING ? (
              <div className="generating-message">
                Crafting this scene... This may take a minute.
              </div>
            ) : scene.status === SceneStatus.FAILED ? (
              <div className="error-message">
                <p>Generation failed: {scene.error}</p>
              </div>
            ) : (
              <div className="pending-message">
                This scene is waiting to be generated.
              </div>
            )}
          </div>
        ) : (
          <div className="scene-metadata">
            <div className="metadata-item">
              <h4>Scene Heading</h4>
              <p>{scene.heading}</p>
            </div>
            <div className="metadata-item">
              <h4>Setting</h4>
              <p>{scene.setting}</p>
            </div>
            <div className="metadata-item">
              <h4>Characters</h4>
              <p>{scene.characters}</p>
            </div>
            <div className="metadata-item">
              <h4>Key Events</h4>
              <p>{scene.key_events}</p>
            </div>
            <div className="metadata-item">
              <h4>Emotional Tone</h4>
              <p>{scene.emotional_tone}</p>
            </div>
          </div>
        )
      )}
    </div>
  );
};

export default SceneView;
