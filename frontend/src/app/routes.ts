/**
 * Application routes configuration
 * Centralizes all route definitions for easier maintenance and consistency
 */

export const ROUTES = {
  HOME: '/',
  CONTENT_LIST: '/content',
  CONTENT_CREATE: '/content/create',
  CONTENT_VIEW: '/content/:id',
  SECTION_VIEW: '/content/:contentId/section/:sectionId',
  SCENE_VIEW: '/content/:contentId/section/:sectionId/scene/:sceneId',
};

// Helper functions to generate actual route paths with parameters
export const generatePath = {
  contentView: (id: string): string => `/content/${id}`,
  sectionView: (contentId: string, sectionId: string): string => 
    `/content/${contentId}/section/${sectionId}`,
  sceneView: (contentId: string, sectionId: string, sceneId: string): string => 
    `/content/${contentId}/section/${sectionId}/scene/${sceneId}`,
};
