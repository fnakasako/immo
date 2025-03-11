/**
 * Main App Component
 * Sets up routing and global layout
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from './routes';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import ContentErrorBoundary from '@/features/content/components/ContentErrorBoundary';

// Import components
import ContentList from '@/features/content/components/ContentList';
import ContentForm from '@/features/content/components/ContentForm';
import ContentViewer from '@/features/content/components/ContentViewer';
import SectionView from '@/features/sections/components/SectionView';
import SceneView from '@/features/scenes/components/SceneView';

// Import styles
import '@/App.css';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="app-container">
        <header className="app-header">
          <h1>Immo</h1>
          <p>An AI Writing Tool</p>
        </header>
        
        <main className="app-main">
          <ErrorBoundary>
            <Routes>
              <Route path={ROUTES.HOME} element={<Navigate to={ROUTES.CONTENT_LIST} />} />
              
              {/* Content routes with ContentErrorBoundary */}
              <Route 
                path={ROUTES.CONTENT_LIST} 
                element={
                  <ContentErrorBoundary>
                    <ContentList />
                  </ContentErrorBoundary>
                } 
              />
              <Route 
                path={ROUTES.CONTENT_CREATE} 
                element={
                  <ContentErrorBoundary>
                    <ContentForm />
                  </ContentErrorBoundary>
                } 
              />
              <Route 
                path={ROUTES.CONTENT_VIEW} 
                element={
                  <ContentErrorBoundary>
                    <ContentViewer />
                  </ContentErrorBoundary>
                } 
              />
              
              {/* These components need to be updated to use params from the URL */}
              <Route path={ROUTES.SECTION_VIEW} element={<div>Section View (Needs params)</div>} />
              <Route path={ROUTES.SCENE_VIEW} element={<div>Scene View (Needs params)</div>} />
            </Routes>
          </ErrorBoundary>
        </main>
        
        <footer className="app-footer">
          <p>Immo: MVP</p>
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
