# Frontend Architecture Refactoring

This project is undergoing a major refactoring to improve scalability, maintainability, and testability. This document outlines the new architecture and provides guidance for completing the refactoring.

## New Architecture Overview

The new architecture follows a feature-based organization with clear separation of concerns:

```
frontend/
├── src/
│   ├── app/                    # App-wide setup and configuration
│   │   ├── App.tsx             # Main app component with routing
│   │   ├── routes.ts           # Route definitions
│   │   └── config.ts           # App configuration (API URLs, etc.)
│   ├── components/             # Shared/common components
│   │   ├── ui/                 # UI primitives (buttons, inputs, etc.)
│   │   └── layout/             # Layout components
│   ├── features/               # Feature-based modules
│   │   ├── content/            # Content feature
│   │   │   ├── components/     # Components specific to content
│   │   │   ├── hooks/          # Custom hooks for content
│   │   │   ├── api/            # API functions for content
│   │   │   ├── types.ts        # Types for content feature
│   │   │   └── utils.ts        # Utilities for content feature
│   │   ├── sections/           # Sections feature
│   │   └── scenes/             # Scenes feature
│   ├── hooks/                  # Shared hooks
│   ├── services/               # Service layer
│   │   ├── api/                # API client and utilities
│   │   │   ├── client.ts       # Base API client
│   │   │   ├── endpoints.ts    # API endpoints
│   │   │   └── types.ts        # API types
│   │   └── auth/               # Authentication service
│   ├── store/                  # State management
│   │   ├── index.ts            # Store setup
│   │   └── slices/             # State slices
│   ├── types/                  # Shared types
│   └── utils/                  # Shared utilities
```

## Completed Refactoring Steps

1. Set up the basic folder structure
2. Created configuration files:
   - `app/config.ts` - Centralized configuration
   - `app/routes.ts` - Route definitions
3. Implemented API layer:
   - `services/api/client.ts` - Base API client with error handling
   - `services/api/endpoints.ts` - API endpoint definitions
   - Feature-specific API modules:
     - `features/content/api/contentApi.ts`
     - `features/sections/api/sectionsApi.ts`
     - `features/scenes/api/scenesApi.ts`
4. Set up routing in `app/App.tsx`
5. Updated `index.tsx` to use the new App component
6. Added global styles in `styles/index.css`

## Next Steps

### 1. Install Required Dependencies

```bash
npm install react-router-dom @reduxjs/toolkit react-redux
```

### 2. Implement State Management

Create Redux store and slices:

```typescript
// src/store/index.ts
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
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### 3. Create Custom Hooks

Implement feature-specific hooks that use the Redux store and API services:

```typescript
// src/features/content/hooks/useContent.ts
import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store';
import {
  fetchContentList,
  fetchContentById,
  // other thunks...
} from '@/store/slices/contentSlice';
import { ContentGenerationRequest } from '@/types';
import { contentApi } from '../api/contentApi';

export const useContent = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { items, currentContent, loading, error } = useSelector(
    (state: RootState) => state.content
  );

  // Implement methods that use the store and API
  // ...
};
```

### 4. Migrate Components

Move existing components to the feature-based structure and update them to use the new architecture:

1. Move `ContentList.tsx` to `features/content/components/ContentList.tsx`
2. Move `ContentForm.tsx` to `features/content/components/ContentForm.tsx`
3. Move `ContentViewer.tsx` to `features/content/components/ContentViewer.tsx`
4. Move `SectionView.tsx` to `features/sections/components/SectionView.tsx`
5. Move `SceneView.tsx` to `features/scenes/components/SceneView.tsx`

Update the components to:
- Use React Router for navigation
- Use custom hooks for data fetching and state management
- Use the new API modules

### 5. Update Index.tsx

Update `index.tsx` to include the Redux Provider:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { store } from './store';
import App from './app/App';
import './styles/index.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);
```

## Benefits of the New Architecture

1. **Scalability**: The feature-based organization makes it easier to add new features without affecting existing ones.
2. **Maintainability**: Clear separation of concerns and consistent patterns make the codebase easier to maintain.
3. **Testability**: The architecture makes it easier to write unit and integration tests.
4. **Developer Experience**: Consistent patterns and organization improve developer productivity.
5. **Performance**: Code splitting and lazy loading can be easily implemented with this architecture.

## Additional Recommendations

1. **Add TypeScript Path Aliases**: Configure TypeScript to use path aliases for cleaner imports.
2. **Implement Testing**: Add Jest and React Testing Library for unit and integration tests.
3. **Add Error Boundary Components**: Implement error boundaries to gracefully handle runtime errors.
4. **Consider Server-Side Rendering**: For better SEO and performance, consider Next.js.
5. **Implement Code Splitting**: Use React.lazy and Suspense for code splitting.
6. **Add Internationalization**: Consider react-i18next for multi-language support.
7. **Implement Design System**: Create a consistent design system with reusable UI components.
