// src/components/SectionView.tsx
import React, { useState, useEffect } from 'react';
import { contentApi } from '../api/contentApi';
import SceneView from './SceneView';
import { SectionResponse, SceneResponse } from '../../types';
import '../styles/SectionView.css';

interface SectionViewProps {
  contentId: string;
  section: SectionResponse;
  isActive: boolean;
}

const SectionView: React.FC<SectionViewProps> = ({ contentId, section, isActive }) => {
  const [expanded, setExpanded] = useState<boolean>(isActive);
  const [scenes, setScenes] = useState<SceneResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeScene, setActiveScene] = useState<number | null>(null);

  useEffect(() => {
    if (expanded && scenes.length === 0) {
      loadScenes();
    }
  }, [expanded]);

  useEffect(() => {
    setExpanded(isActive);
  }, [isActive]);

  const loadScenes = async (): Promise<void> => {
    if (!contentId || !section) return;
    
    setLoading(true);
    try {
      const response = await contentApi.getScenes(contentId, section.number);
      setScenes(response.scenes);
      if (response.scenes.length > 0) {
        setActiveScene(1);
      }
    } catch (error) {
      console.error('Failed to load scenes:', error);
    } finally {
      setLoading(false);
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
      <div className="section-header" onClick={toggleExpand}>
        <div className="section-title">
          <span className={`status-indicator ${getStatusClass()}`} />
          <h3>Section {section.number}: {section.title}</h3>
        </div>
        <div className="section-controls">
          <button className="expand-button">
            {expanded ? '▼' : '►'}
          </button>
        </div>
      </div>
      
      {expanded && (
        <div className="section-content">
          <div className="section-summary">
            <h4>Summary</h4>
            <p>{section.summary}</p>
          </div>
          
          {loading ? (
            <div className="loading">Loading scenes...</div>
          ) : (
            <>
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
