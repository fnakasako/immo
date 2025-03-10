// src/App.tsx
import React, { useState } from 'react';
import ContentForm from './components/ContentForm';
import ContentViewer from './components/ContentViewer';
import ContentList from './components/ContentList';
import { contentApi } from './api/contentApi';
import { ContentGenerationRequest } from '../types';
import './App.css';

// Define the possible app states
type AppState = 'list' | 'form' | 'view';

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>('list');
  const [contentId, setContentId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (formData: ContentGenerationRequest): Promise<void> => {
    setSubmitting(true);
    setError(null);
    
    try {
      const response = await contentApi.createContent(formData);
      setContentId(response.id);
      setAppState('view');
    } catch (error) {
      console.error('Content creation failed:', error);
      // Display the specific error message from the API
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('Failed to create content');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectContent = (id: string): void => {
    setContentId(id);
    setAppState('view');
  };

  const handleCreateNew = (): void => {
    setContentId(null);
    setError(null);
    setAppState('form');
  };

  const handleBackToList = (): void => {
    setAppState('list');
  };

  const renderContent = () => {
    switch (appState) {
      case 'list':
        return (
          <ContentList 
            onSelectContent={handleSelectContent} 
            onCreateNew={handleCreateNew} 
          />
        );
      case 'form':
        return (
          <>
            <ContentForm 
              onSubmit={handleSubmit} 
              isSubmitting={submitting} 
            />
            
            {error && (
              <div className="error-message">
                <p>{error}</p>
              </div>
            )}
            <div className="back-button-container">
              <button className="back-button" onClick={handleBackToList}>
                Back to Content List
              </button>
            </div>
          </>
        );
      case 'view':
        return contentId ? (
          <>
            <ContentViewer 
              contentId={contentId} 
              onReset={handleCreateNew} 
            />
            <div className="back-button-container">
              <button className="back-button" onClick={handleBackToList}>
                Back to Content List
              </button>
            </div>
          </>
        ) : (
          <div className="error-message">
            <p>No content selected</p>
            <button onClick={handleBackToList}>Back to Content List</button>
          </div>
        );
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Immo</h1>
        <p>An AI Writing Tool</p>
      </header>
      
      <main className="app-main">
        {renderContent()}
      </main>
      
      <footer className="app-footer">
        <p>Immo: MVP</p>
      </footer>
    </div>
  );
};

export default App;
