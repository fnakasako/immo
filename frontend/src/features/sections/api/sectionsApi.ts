/**
 * Sections API
 * Provides methods for interacting with the section-related endpoints
 */
import { apiRequest } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import {
  SectionResponse,
  SectionListResponse,
  SectionUpdateRequest,
  SceneListResponse
} from '@/types';

export const sectionsApi = {
  /**
   * Get all sections for a content
   */
  getSections: (contentId: string): Promise<SectionListResponse> => 
    apiRequest.get(ENDPOINTS.SECTIONS.LIST(contentId)),
  
  /**
   * Get a specific section
   */
  getSection: (contentId: string, sectionNumber: number): Promise<SectionResponse> => 
    apiRequest.get(ENDPOINTS.SECTIONS.DETAIL(contentId, sectionNumber)),
  
  /**
   * Update a section
   */
  updateSection: (contentId: string, sectionNumber: number, data: SectionUpdateRequest): Promise<SectionResponse> => 
    apiRequest.put(ENDPOINTS.SECTIONS.UPDATE(contentId, sectionNumber), data),
  
  /**
   * Get scenes for a section
   */
  getScenes: (contentId: string, sectionNumber: number): Promise<SceneListResponse> => 
    apiRequest.get(ENDPOINTS.SCENES.LIST(contentId, sectionNumber)),
};
