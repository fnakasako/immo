/**
 * API Endpoints
 * Centralizes all API endpoint definitions for easier maintenance and consistency
 */

export const ENDPOINTS = {
  CONTENT: {
    LIST: '/content',
    DETAIL: (id: string) => `/content/${id}`,
    CREATE: '/content',
    GENERATE_OUTLINE: (id: string) => `/content/${id}/generate-outline`,
    UPDATE_OUTLINE: (id: string) => `/content/${id}/outline`,
    GENERATE_SECTIONS: (id: string) => `/content/${id}/generate-sections`,
    GENERATE_SCENES: (id: string) => `/content/${id}/generate-scenes`,
  },
  SECTIONS: {
    LIST: (contentId: string) => `/content/${contentId}/sections`,
    DETAIL: (contentId: string, sectionNumber: number) => 
      `/content/${contentId}/sections/${sectionNumber}`,
    UPDATE: (contentId: string, sectionNumber: number) => 
      `/content/${contentId}/sections/${sectionNumber}`,
  },
  SCENES: {
    LIST: (contentId: string, sectionNumber: number) => 
      `/content/${contentId}/sections/${sectionNumber}/scenes`,
    DETAIL: (contentId: string, sectionNumber: number, sceneNumber: number) => 
      `/content/${contentId}/sections/${sectionNumber}/scenes/${sceneNumber}`,
    UPDATE: (contentId: string, sectionNumber: number, sceneNumber: number) => 
      `/content/${contentId}/sections/${sectionNumber}/scenes/${sceneNumber}`,
    GENERATE_PROSE: (contentId: string, sectionNumber: number) => 
      `/content/${contentId}/sections/${sectionNumber}/generate-prose`,
  },
};
