/**
 * Content Hook
 * Provides methods for interacting with content-related data and operations
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchContentList,
  fetchContentById,
  createContent,
  generateOutline,
  updateOutline,
  generateSections,
  generateScenes,
  clearCurrentContent,
  clearError
} from '@/store/slices/contentSlice';
import { 
  ContentGenerationRequest, 
  ContentUpdateRequest 
} from '@/types';

export const useContent = () => {
  const dispatch = useAppDispatch();
  const { 
    items, 
    currentContent, 
    loading, 
    error 
  } = useAppSelector(state => state.content);

  // Get content list
  const getContentList = useCallback((skip?: number, limit?: number) => {
    return dispatch(fetchContentList({ skip, limit }));
  }, [dispatch]);

  // Get content by ID
  const getContentById = useCallback((contentId: string) => {
    return dispatch(fetchContentById(contentId));
  }, [dispatch]);

  // Create new content
  const createNewContent = useCallback((data: ContentGenerationRequest) => {
    return dispatch(createContent(data));
  }, [dispatch]);

  // Generate outline
  const generateContentOutline = useCallback((contentId: string) => {
    return dispatch(generateOutline(contentId));
  }, [dispatch]);

  // Update outline
  const updateContentOutline = useCallback((contentId: string, data: ContentUpdateRequest) => {
    return dispatch(updateOutline({ contentId, data }));
  }, [dispatch]);

  // Generate sections
  const generateContentSections = useCallback((contentId: string) => {
    return dispatch(generateSections(contentId));
  }, [dispatch]);

  // Generate scenes
  const generateContentScenes = useCallback((contentId: string, sectionNumbers: number[]) => {
    return dispatch(generateScenes({ contentId, sectionNumbers }));
  }, [dispatch]);

  // Clear current content
  const clearContent = useCallback(() => {
    dispatch(clearCurrentContent());
  }, [dispatch]);

  // Clear error
  const clearContentError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    // State
    contentList: items,
    currentContent,
    loading,
    error,
    
    // Methods
    getContentList,
    getContentById,
    createContent: createNewContent,
    generateOutline: generateContentOutline,
    updateOutline: updateContentOutline,
    generateSections: generateContentSections,
    generateScenes: generateContentScenes,
    clearContent,
    clearError: clearContentError
  };
};
