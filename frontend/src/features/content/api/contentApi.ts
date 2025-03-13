/**
 * Content API
 * Provides methods for interacting with the content-related endpoints
 */
import { apiRequest } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import {
  ContentGenerationRequest,
  ContentGenerationResponse,
  ContentUpdateRequest,
  GenerationSelectionRequest,
  SectionListResponse
} from '@/types';

export const contentApi = {
  /**
   * List all content generations
   */
  listContent: (skip: number = 0, limit: number = 10): Promise<ContentGenerationResponse[]> => 
    apiRequest.get(`${ENDPOINTS.CONTENT.LIST}?skip=${skip}&limit=${limit}`),
  
  /**
   * Create new content generation (without starting generation)
   */
  createContent: (requestData: ContentGenerationRequest): Promise<ContentGenerationResponse> => 
    apiRequest.post(ENDPOINTS.CONTENT.CREATE, requestData),
  
  /**
   * Generate outline for content
   */
  generateOutline: (contentId: string): Promise<ContentGenerationResponse> => 
    apiRequest.post(ENDPOINTS.CONTENT.GENERATE_OUTLINE(contentId)),
  
  /**
   * Update content outline
   */
  updateOutline: (contentId: string, data: ContentUpdateRequest): Promise<ContentGenerationResponse> => 
    apiRequest.put(ENDPOINTS.CONTENT.UPDATE_OUTLINE(contentId), data),
  
  /**
   * Generate sections for content
   * @param contentId The ID of the content
   * @param numSections Optional number of sections to generate
   */
  generateSections: (contentId: string, numSections?: number): Promise<SectionListResponse> => 
    apiRequest.post(ENDPOINTS.CONTENT.GENERATE_SECTIONS(contentId), numSections ? { numSections } : undefined),
  
  /**
   * Generate scenes for selected sections
   */
  generateScenes: (contentId: string, sectionNumbers: number[]): Promise<SectionListResponse> => 
    apiRequest.post(
      ENDPOINTS.CONTENT.GENERATE_SCENES(contentId), 
      { items: sectionNumbers } as GenerationSelectionRequest
    ),
  
  /**
   * Get content generation status
   */
  getContent: (contentId: string): Promise<ContentGenerationResponse> => 
    apiRequest.get(ENDPOINTS.CONTENT.DETAIL(contentId)),
};
