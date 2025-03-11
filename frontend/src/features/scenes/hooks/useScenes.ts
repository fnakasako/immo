/**
 * Scenes Hook
 * Provides methods for interacting with scene-related data and operations
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchSceneById,
  updateScene,
  generateProse,
  setScenes,
  clearCurrentScene,
  clearError
} from '@/store/slices/scenesSlice';
import { SceneUpdateRequest, SceneListResponse } from '@/types';

export const useScenes = () => {
  const dispatch = useAppDispatch();
  const { 
    items, 
    currentScene, 
    loading, 
    error,
    total
  } = useAppSelector((state: any) => state.scenes);

  // Set scenes from external source (e.g., sections slice)
  const setScenesList = useCallback((scenesList: SceneListResponse) => {
    dispatch(setScenes(scenesList));
  }, [dispatch]);

  // Get scene by ID
  const getSceneById = useCallback((
    contentId: string, 
    sectionNumber: number, 
    sceneNumber: number
  ) => {
    return dispatch(fetchSceneById({ contentId, sectionNumber, sceneNumber }));
  }, [dispatch]);

  // Update scene
  const updateSceneData = useCallback((
    contentId: string, 
    sectionNumber: number, 
    sceneNumber: number, 
    data: SceneUpdateRequest
  ) => {
    return dispatch(updateScene({ contentId, sectionNumber, sceneNumber, data }));
  }, [dispatch]);

  // Generate prose for scenes
  const generateSceneProse = useCallback((
    contentId: string, 
    sectionNumber: number, 
    sceneNumbers: number[]
  ) => {
    return dispatch(generateProse({ contentId, sectionNumber, sceneNumbers }));
  }, [dispatch]);

  // Clear current scene
  const clearScene = useCallback(() => {
    dispatch(clearCurrentScene());
  }, [dispatch]);

  // Clear error
  const clearSceneError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    // State
    scenes: items,
    currentScene,
    loading,
    error,
    total,
    
    // Methods
    setScenes: setScenesList,
    getSceneById,
    updateScene: updateSceneData,
    generateProse: generateSceneProse,
    clearScene,
    clearError: clearSceneError
  };
};
