/**
 * Redux Store Configuration
 * Centralizes the Redux store setup and exports types for use throughout the application
 */
import { configureStore } from '@reduxjs/toolkit';
import contentReducer from './slices/contentSlice';
import sectionsReducer from './slices/sectionsSlice';
import scenesReducer from './slices/scenesSlice';

export const store = configureStore({
  reducer: {
    content: contentReducer,
    sections: sectionsReducer,
    scenes: scenesReducer,
  },
  // Add middleware or other configuration options here
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // Disable serializable check for non-serializable values
    }),
});

// Export types for use in the application
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export typed hooks for use in components
export * from './hooks';
