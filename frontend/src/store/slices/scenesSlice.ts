/**
 * Scenes Slice
 * Manages the state for scene-related data and operations
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { scenesApi } from '@/features/scenes/api/scenesApi';
import { 
  SceneResponse, 
  SceneListResponse,
  SceneUpdateRequest,
  SceneStatus
} from '@/types';

// Define the state interface
interface ScenesState {
  items: SceneResponse[];
  currentScene: SceneResponse | null;
  loading: boolean;
  error: string | null;
  total: number;
}

// Initial state
const initialState: ScenesState = {
  items: [],
  currentScene: null,
  loading: false,
  error: null,
  total: 0,
};

// Async thunks
export const fetchSceneById = createAsyncThunk(
  'scenes/fetchById',
  async ({ 
    contentId, 
    sectionNumber, 
    sceneNumber 
  }: { 
    contentId: string; 
    sectionNumber: number; 
    sceneNumber: number 
  }) => {
    return await scenesApi.getScene(contentId, sectionNumber, sceneNumber);
  }
);

export const updateScene = createAsyncThunk(
  'scenes/update',
  async ({ 
    contentId, 
    sectionNumber, 
    sceneNumber, 
    data 
  }: { 
    contentId: string; 
    sectionNumber: number; 
    sceneNumber: number; 
    data: SceneUpdateRequest 
  }) => {
    return await scenesApi.updateScene(contentId, sectionNumber, sceneNumber, data);
  }
);

export const generateProse = createAsyncThunk(
  'scenes/generateProse',
  async ({ 
    contentId, 
    sectionNumber, 
    sceneNumbers 
  }: { 
    contentId: string; 
    sectionNumber: number; 
    sceneNumbers: number[] 
  }) => {
    return await scenesApi.generateProse(contentId, sectionNumber, sceneNumbers);
  }
);

// Create the slice
const scenesSlice = createSlice({
  name: 'scenes',
  initialState,
  reducers: {
    setScenes: (state, action: PayloadAction<SceneListResponse>) => {
      state.items = action.payload.scenes;
      state.total = action.payload.total;
    },
    clearCurrentScene: (state) => {
      state.currentScene = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Handle fetchSceneById
    builder.addCase(fetchSceneById.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchSceneById.fulfilled, (state, action) => {
      state.loading = false;
      state.currentScene = action.payload;
    });
    builder.addCase(fetchSceneById.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch scene';
    });

    // Handle updateScene
    builder.addCase(updateScene.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(updateScene.fulfilled, (state, action) => {
      state.loading = false;
      state.currentScene = action.payload;
      
      // Update the scene in the items array if it exists
      const index = state.items.findIndex(scene => scene.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
    });
    builder.addCase(updateScene.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to update scene';
    });

    // Handle generateProse
    builder.addCase(generateProse.pending, (state, action) => {
      state.loading = true;
      state.error = null;
      
      // Update the status of the selected scenes
      state.items.forEach(scene => {
        if (action.meta.arg.sceneNumbers.includes(scene.number)) {
          scene.status = SceneStatus.GENERATING;
        }
      });
    });
    builder.addCase(generateProse.fulfilled, (state, action) => {
      state.loading = false;
      
      // Update the scenes with the generated prose
      action.payload.scenes.forEach(updatedScene => {
        const index = state.items.findIndex(scene => scene.id === updatedScene.id);
        if (index !== -1) {
          state.items[index] = updatedScene;
        }
      });
      
      // If the current scene is one of the updated scenes, update it
      if (state.currentScene && action.payload.scenes.some(scene => scene.id === state.currentScene?.id)) {
        const updatedScene = action.payload.scenes.find(scene => scene.id === state.currentScene?.id);
        if (updatedScene) {
          state.currentScene = updatedScene;
        }
      }
    });
    builder.addCase(generateProse.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to generate prose';
      
      // Update the status of the selected scenes to failed
      state.items.forEach(scene => {
        if (action.meta.arg.sceneNumbers.includes(scene.number)) {
          scene.status = SceneStatus.FAILED;
        }
      });
    });
  },
});

// Export actions and reducer
export const { setScenes, clearCurrentScene, clearError } = scenesSlice.actions;
export default scenesSlice.reducer;
