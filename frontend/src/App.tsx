// src/App.tsx
import React, { useState } from 'react';
import ContentForm from './components/ContentForm';
import ContentViewer from './components/ContentViewer';
import { contentApi } from './api/contentApi';
import { ContentGenerationRequest } from '../types';
import './App.css';

const App: React.FC = () => {
  const [contentId, setContentId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (formData: ContentGenerationRequest): Promise<void> => {
    setSubmitting(true);
    setError(null);
    
    try {
      const response = await contentApi.createContent(formData);
      setContentId(response.id);
    } catch (error) {
      console.error('Content creation failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to create content');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = (): void => {
    setContentId(null);
    setError(null);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Immo</h1>
        <p>An AI Writing Tool</p>
      </header>
      
      <main className="app-main">
        {!contentId ? (
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
          </>
        ) : (
          <ContentViewer 
            contentId={contentId} 
            onReset={handleReset} 
          />
        )}
      </main>
      
      <footer className="app-footer">
        <p>AI-Powered Immo - MVP Version</p>
      </footer>
    </div>
  );
};

export default App;
