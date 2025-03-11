/**
 * Sections Slice
 * Manages the state for section-related data and operations
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { sectionsApi } from '@/features/sections/api/sectionsApi';
import { 
  SectionResponse, 
  SectionListResponse,
  SectionUpdateRequest,
  SectionStatus,
  SceneListResponse
} from '@/types';

// Define the state interface
interface SectionsState {
  items: SectionResponse[];
  currentSection: SectionResponse | null;
  scenes: SceneListResponse | null;
  loading: boolean;
  error: string | null;
  total: number;
}

// Initial state
const initialState: SectionsState = {
  items: [],
  currentSection: null,
  scenes: null,
  loading: false,
  error: null,
  total: 0,
};

// Async thunks
export const fetchSections = createAsyncThunk(
  'sections/fetchAll',
  async (contentId: string) => {
    return await sectionsApi.getSections(contentId);
  }
);

export const fetchSectionById = createAsyncThunk(
  'sections/fetchById',
  async ({ contentId, sectionNumber }: { contentId: string; sectionNumber: number }) => {
    return await sectionsApi.getSection(contentId, sectionNumber);
  }
);

export const updateSection = createAsyncThunk(
  'sections/update',
  async ({ 
    contentId, 
    sectionNumber, 
    data 
  }: { 
    contentId: string; 
    sectionNumber: number; 
    data: SectionUpdateRequest 
  }) => {
    return await sectionsApi.updateSection(contentId, sectionNumber, data);
  }
);

export const fetchScenes = createAsyncThunk(
  'sections/fetchScenes',
  async ({ contentId, sectionNumber }: { contentId: string; sectionNumber: number }) => {
    return await sectionsApi.getScenes(contentId, sectionNumber);
  }
);

// Create the slice
const sectionsSlice = createSlice({
  name: 'sections',
  initialState,
  reducers: {
    clearCurrentSection: (state) => {
      state.currentSection = null;
      state.scenes = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Handle fetchSections
    builder.addCase(fetchSections.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchSections.fulfilled, (state, action) => {
      state.loading = false;
      state.items = action.payload.sections;
      state.total = action.payload.total;
    });
    builder.addCase(fetchSections.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch sections';
    });

    // Handle fetchSectionById
    builder.addCase(fetchSectionById.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchSectionById.fulfilled, (state, action) => {
      state.loading = false;
      state.currentSection = action.payload;
    });
    builder.addCase(fetchSectionById.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch section';
    });

    // Handle updateSection
    builder.addCase(updateSection.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(updateSection.fulfilled, (state, action) => {
      state.loading = false;
      state.currentSection = action.payload;
      
      // Update the section in the items array if it exists
      const index = state.items.findIndex(section => section.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
    });
    builder.addCase(updateSection.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to update section';
    });

    // Handle fetchScenes
    builder.addCase(fetchScenes.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchScenes.fulfilled, (state, action) => {
      state.loading = false;
      state.scenes = action.payload;
    });
    builder.addCase(fetchScenes.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch scenes';
    });
  },
});

// Export actions and reducer
export const { clearCurrentSection, clearError } = sectionsSlice.actions;
export default sectionsSlice.reducer;
