/**
 * Scenes API
 * Provides methods for interacting with the scene-related endpoints
 */
import { apiRequest } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import {
  SceneResponse,
  SceneListResponse,
  SceneUpdateRequest,
  GenerationSelectionRequest
} from '@/types';

export const scenesApi = {
  /**
   * Get a specific scene
   */
  getScene: (contentId: string, sectionNumber: number, sceneNumber: number): Promise<SceneResponse> => 
    apiRequest.get(ENDPOINTS.SCENES.DETAIL(contentId, sectionNumber, sceneNumber)),
  
  /**
   * Update a scene
   */
  updateScene: (
    contentId: string, 
    sectionNumber: number, 
    sceneNumber: number, 
    data: SceneUpdateRequest
  ): Promise<SceneResponse> => 
    apiRequest.put(ENDPOINTS.SCENES.UPDATE(contentId, sectionNumber, sceneNumber), data),
  
  /**
   * Generate prose for selected scenes
   */
  generateProse: (
    contentId: string, 
    sectionNumber: number, 
    sceneNumbers: number[]
  ): Promise<SceneListResponse> => 
    apiRequest.post(
      ENDPOINTS.SCENES.GENERATE_PROSE(contentId, sectionNumber), 
      { items: sceneNumbers } as GenerationSelectionRequest
    ),
};
