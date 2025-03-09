// src/api/contentApi.ts
import {
    ContentGenerationRequest,
    ContentGenerationResponse,
    SectionListResponse,
    SectionResponse,
    SceneListResponse,
    SceneResponse
  } from '../types';
  
  const API_BASE = '/api';
  
  export const contentApi = {
    // Create new content generation
    createContent: async (requestData: ContentGenerationRequest): Promise<ContentGenerationResponse> => {
      const response = await fetch(`${API_BASE}/content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create content');
      }
      
      return response.json();
    },
    
    // Get content generation status
    getContent: async (contentId: string): Promise<ContentGenerationResponse> => {
      const response = await fetch(`${API_BASE}/content/${contentId}`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch content');
      }
      
      return response.json();
    },
    
    // Get all sections
    getSections: async (contentId: string): Promise<SectionListResponse> => {
      const response = await fetch(`${API_BASE}/content/${contentId}/sections`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch sections');
      }
      
      return response.json();
    },
    
    // Get a specific section
    getSection: async (contentId: string, sectionNumber: number): Promise<SectionResponse> => {
      const response = await fetch(`${API_BASE}/content/${contentId}/sections/${sectionNumber}`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch section');
      }
      
      return response.json();
    },
    
    // Get scenes for a section
    getScenes: async (contentId: string, sectionNumber: number): Promise<SceneListResponse> => {
      const response = await fetch(`${API_BASE}/content/${contentId}/sections/${sectionNumber}/scenes`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch scenes');
      }
      
      return response.json();
    },
    
    // Get a specific scene
    getScene: async (contentId: string, sectionNumber: number, sceneNumber: number): Promise<SceneResponse> => {
      const response = await fetch(`${API_BASE}/content/${contentId}/sections/${sectionNumber}/scenes/${sceneNumber}`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch scene');
      }
      
      return response.json();
    }
  };