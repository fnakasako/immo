/**
 * Content Slice
 * Manages the state for content-related data and operations
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { contentApi } from '@/features/content/api/contentApi';
import { getUserFriendlyErrorMessage } from '@/services/api/errors';
import { 
  ContentGenerationResponse, 
  ContentGenerationRequest,
  ContentUpdateRequest,
  GenerationStatus
} from '@/types';

// Define the state interface
interface ContentState {
  items: ContentGenerationResponse[];
  currentContent: ContentGenerationResponse | null;
  loading: boolean;
  error: string | null;
}

// Initial state
const initialState: ContentState = {
  items: [],
  currentContent: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchContentList = createAsyncThunk(
  'content/fetchList',
  async ({ skip, limit }: { skip?: number; limit?: number } = {}) => {
    return await contentApi.listContent(skip, limit);
  }
);

export const fetchContentById = createAsyncThunk(
  'content/fetchById',
  async (contentId: string) => {
    return await contentApi.getContent(contentId);
  }
);

export const createContent = createAsyncThunk(
  'content/create',
  async (data: ContentGenerationRequest) => {
    const response = await contentApi.createContent(data);
    return response;
  }
);

export const generateOutline = createAsyncThunk(
  'content/generateOutline',
  async (contentId: string) => {
    return await contentApi.generateOutline(contentId);
  }
);

export const updateOutline = createAsyncThunk(
  'content/updateOutline',
  async ({ contentId, data }: { contentId: string; data: ContentUpdateRequest }) => {
    return await contentApi.updateOutline(contentId, data);
  }
);

export const generateSections = createAsyncThunk(
  'content/generateSections',
  async ({ contentId, numSections }: { contentId: string; numSections?: number }, { dispatch }) => {
    try {
      const sectionsResponse = await contentApi.generateSections(contentId, numSections);
      // Fetch the updated content status after generating sections
      await dispatch(fetchContentById(contentId)).unwrap();
      return sectionsResponse;
    } catch (error) {
      // Re-throw the error to be caught by the rejected case
      throw error;
    }
  }
);

export const generateScenes = createAsyncThunk(
  'content/generateScenes',
  async ({ contentId, sectionNumbers }: { contentId: string; sectionNumbers: number[] }, { dispatch }) => {
    try {
      const scenesResponse = await contentApi.generateScenes(contentId, sectionNumbers);
      // Fetch the updated content status after generating scenes
      await dispatch(fetchContentById(contentId)).unwrap();
      return scenesResponse;
    } catch (error) {
      // Re-throw the error to be caught by the rejected case
      throw error;
    }
  }
);

// Create the slice
const contentSlice = createSlice({
  name: 'content',
  initialState,
  reducers: {
    clearCurrentContent: (state) => {
      state.currentContent = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Handle fetchContentList
    builder.addCase(fetchContentList.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchContentList.fulfilled, (state, action) => {
      state.loading = false;
      state.items = action.payload;
    });
    builder.addCase(fetchContentList.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch content list';
    });

    // Handle fetchContentById
    builder.addCase(fetchContentById.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchContentById.fulfilled, (state, action) => {
      state.loading = false;
      state.currentContent = action.payload;
    });
    builder.addCase(fetchContentById.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message ? 
        getUserFriendlyErrorMessage(new Error(action.error.message)) : 
        'Failed to fetch content';
    });

    // Handle createContent
    builder.addCase(createContent.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(createContent.fulfilled, (state, action) => {
      state.loading = false;
      state.currentContent = action.payload;
    });
    builder.addCase(createContent.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to create content';
    });

    // Handle generateOutline
    builder.addCase(generateOutline.pending, (state) => {
      state.loading = true;
      state.error = null;
      if (state.currentContent) {
        state.currentContent.status = GenerationStatus.PROCESSING_OUTLINE;
      }
    });
    builder.addCase(generateOutline.fulfilled, (state, action) => {
      state.loading = false;
      state.currentContent = action.payload;
    });
    builder.addCase(generateOutline.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to generate outline';
      if (state.currentContent) {
        state.currentContent.status = GenerationStatus.FAILED;
      }
    });

    // Handle updateOutline
    builder.addCase(updateOutline.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(updateOutline.fulfilled, (state, action) => {
      state.loading = false;
      state.currentContent = action.payload;
    });
    builder.addCase(updateOutline.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to update outline';
    });

    // Handle generateSections
    builder.addCase(generateSections.pending, (state) => {
      state.loading = true;
      state.error = null;
      if (state.currentContent) {
        state.currentContent.status = GenerationStatus.PROCESSING_SECTIONS;
      }
    });
    builder.addCase(generateSections.fulfilled, (state) => {
      // Don't set loading to false here as we're fetching content in the thunk
      // The content status will be updated when fetchContentById completes
    });
    builder.addCase(generateSections.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to generate sections';
      if (state.currentContent) {
        state.currentContent.status = GenerationStatus.FAILED;
      }
    });

    // Handle generateScenes
    builder.addCase(generateScenes.pending, (state) => {
      state.loading = true;
      state.error = null;
      if (state.currentContent) {
        state.currentContent.status = GenerationStatus.PROCESSING_SCENES;
      }
    });
    builder.addCase(generateScenes.fulfilled, (state) => {
      // Don't set loading to false here as we're fetching content in the thunk
      // The content status will be updated when fetchContentById completes
    });
    builder.addCase(generateScenes.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to generate scenes';
      if (state.currentContent) {
        state.currentContent.status = GenerationStatus.FAILED;
      }
    });
  },
});

// Export actions and reducer
export const { clearCurrentContent, clearError } = contentSlice.actions;
export default contentSlice.reducer;
