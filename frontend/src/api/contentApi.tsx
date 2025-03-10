// src/api/contentApi.ts
import {
    ContentGenerationRequest,
    ContentGenerationResponse,
    SectionListResponse,
    SectionResponse,
    SceneListResponse,
    SceneResponse
  } from '../../types';
  
  // Use the backend URL (defined in docker-compose.yml as http://localhost:8000)
const API_BASE = 'http://localhost:8000';
const API_PATH = '/api';
  
  export const contentApi = {
    // List all content generations
    listContent: async (skip: number = 0, limit: number = 10): Promise<ContentGenerationResponse[]> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content?skip=${skip}&limit=${limit}`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch content list');
      }
      
      return response.json();
    },
    // Create new content generation
    createContent: async (requestData: ContentGenerationRequest): Promise<ContentGenerationResponse> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });
      
      if (!response.ok) {
        // Try to parse error as JSON, but handle cases where it's not valid JSON
        try {
          const error = await response.json();
          if (response.status === 401) {
            throw new Error(error.detail || 'Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error(error.detail || 'Failed to create content');
        } catch (jsonError) {
          if (response.status === 401) {
            throw new Error('Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error('Failed to create content');
        }
      }
      
      return response.json();
    },
    
    // Get content generation status
    getContent: async (contentId: string): Promise<ContentGenerationResponse> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content/${contentId}`);
      
      if (!response.ok) {
        try {
          const error = await response.json();
          if (response.status === 401) {
            throw new Error(error.detail || 'Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error(error.detail || 'Failed to fetch content');
        } catch (jsonError) {
          if (response.status === 401) {
            throw new Error('Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error('Failed to fetch content');
        }
      }
      
      return response.json();
    },
    
    // Get all sections
    getSections: async (contentId: string): Promise<SectionListResponse> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content/${contentId}/sections`);
      
      if (!response.ok) {
        try {
          const error = await response.json();
          if (response.status === 401) {
            throw new Error(error.detail || 'Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error(error.detail || 'Failed to fetch sections');
        } catch (jsonError) {
          if (response.status === 401) {
            throw new Error('Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error('Failed to fetch sections');
        }
      }
      
      return response.json();
    },
    
    // Get a specific section
    getSection: async (contentId: string, sectionNumber: number): Promise<SectionResponse> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content/${contentId}/sections/${sectionNumber}`);
      
      if (!response.ok) {
        try {
          const error = await response.json();
          if (response.status === 401) {
            throw new Error(error.detail || 'Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error(error.detail || 'Failed to fetch section');
        } catch (jsonError) {
          if (response.status === 401) {
            throw new Error('Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error('Failed to fetch section');
        }
      }
      
      return response.json();
    },
    
    // Get scenes for a section
    getScenes: async (contentId: string, sectionNumber: number): Promise<SceneListResponse> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content/${contentId}/sections/${sectionNumber}/scenes`);
      
      if (!response.ok) {
        try {
          const error = await response.json();
          if (response.status === 401) {
            throw new Error(error.detail || 'Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error(error.detail || 'Failed to fetch scenes');
        } catch (jsonError) {
          if (response.status === 401) {
            throw new Error('Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error('Failed to fetch scenes');
        }
      }
      
      return response.json();
    },
    
    // Get a specific scene
    getScene: async (contentId: string, sectionNumber: number, sceneNumber: number): Promise<SceneResponse> => {
      const response = await fetch(`${API_BASE}${API_PATH}/content/${contentId}/sections/${sectionNumber}/scenes/${sceneNumber}`);
      
      if (!response.ok) {
        try {
          const error = await response.json();
          if (response.status === 401) {
            throw new Error(error.detail || 'Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error(error.detail || 'Failed to fetch scene');
        } catch (jsonError) {
          if (response.status === 401) {
            throw new Error('Invalid API key. Please check your Anthropic API key configuration.');
          }
          throw new Error('Failed to fetch scene');
        }
      }
      
      return response.json();
    }
  };
