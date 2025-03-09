// src/components/SceneView.tsx
import React, { useState, useEffect } from 'react';
import { contentApi } from '../api/contentApi';
import { SceneResponse, SceneStatus } from '../../types';
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

  useEffect(() => {
    loadScene();
  }, [contentId, sectionNumber, sceneNumber]);

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

  if (loading) {
    return <div className="scene-loading">Loading scene...</div>;
  }

  if (error || !scene) {
    return <div className="scene-error">{error || 'Scene not found'}</div>;
  }

  return (
    <div className="scene-view">
      <div className="scene-controls">
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
      
      {viewMode === 'prose' ? (
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
      )}
    </div>
  );
};

export default SceneView;
