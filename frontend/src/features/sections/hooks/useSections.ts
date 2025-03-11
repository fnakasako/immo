/**
 * Sections Hook
 * Provides methods for interacting with section-related data and operations
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchSections,
  fetchSectionById,
  updateSection,
  fetchScenes,
  clearCurrentSection,
  clearError
} from '@/store/slices/sectionsSlice';
import { SectionUpdateRequest } from '@/types';

export const useSections = () => {
  const dispatch = useAppDispatch();
  const { 
    items, 
    currentSection, 
    scenes,
    loading, 
    error,
    total
  } = useAppSelector((state: any) => state.sections);

  // Get all sections for a content
  const getSections = useCallback((contentId: string) => {
    return dispatch(fetchSections(contentId));
  }, [dispatch]);

  // Get section by ID
  const getSectionById = useCallback((contentId: string, sectionNumber: number) => {
    return dispatch(fetchSectionById({ contentId, sectionNumber }));
  }, [dispatch]);

  // Update section
  const updateSectionData = useCallback((
    contentId: string, 
    sectionNumber: number, 
    data: SectionUpdateRequest
  ) => {
    return dispatch(updateSection({ contentId, sectionNumber, data }));
  }, [dispatch]);

  // Get scenes for a section
  const getScenes = useCallback((contentId: string, sectionNumber: number) => {
    return dispatch(fetchScenes({ contentId, sectionNumber }));
  }, [dispatch]);

  // Clear current section
  const clearSection = useCallback(() => {
    dispatch(clearCurrentSection());
  }, [dispatch]);

  // Clear error
  const clearSectionError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    // State
    sections: items,
    currentSection,
    scenes,
    loading,
    error,
    total,
    
    // Methods
    getSections,
    getSectionById,
    updateSection: updateSectionData,
    getScenes,
    clearSection,
    clearError: clearSectionError
  };
};
