# Further Frontend Architecture Improvements

Based on the refactoring work completed so far, here are the next steps to further enhance the frontend architecture. These improvements focus on error handling, performance, and maintainability.

## Phase 1: Error Handling (Priority: High)

### 1. Implement Error Boundaries

Error boundaries are React components that catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of crashing the whole application.

#### Implementation Plan:

1. Create a generic ErrorBoundary component:

```tsx
// src/components/common/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  fallback?: ReactNode;
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return this.props.fallback || (
        <div className="error-boundary-fallback">
          <h2>Something went wrong.</h2>
          <p>Please try refreshing the page or contact support if the problem persists.</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

2. Create feature-specific error boundaries:

```tsx
// src/features/content/components/ContentErrorBoundary.tsx
import React from 'react';
import ErrorBoundary from '@/components/common/ErrorBoundary';

const ContentErrorFallback = () => (
  <div className="content-error-fallback">
    <h3>Error Loading Content</h3>
    <p>We encountered an issue while loading your content. Please try again later.</p>
  </div>
);

const ContentErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ErrorBoundary 
      fallback={<ContentErrorFallback />}
      onError={(error) => {
        // Log to monitoring service
        console.error('Content error:', error);
      }}
    >
      {children}
    </ErrorBoundary>
  );
};

export default ContentErrorBoundary;
```

3. Wrap key components with error boundaries:

```tsx
// In App.tsx or route components
<ContentErrorBoundary>
  <ContentViewer />
</ContentErrorBoundary>
```

### 2. Enhance API Error Handling

Improve the error handling in the API client to provide more detailed error information and better recovery options.

#### Implementation Plan:

1. Create custom error classes:

```tsx
// src/services/api/errors.ts
export class ApiError extends Error {
  status: number;
  data: any;
  
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error occurred') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timed out') {
    super(message);
    this.name = 'TimeoutError';
  }
}
```

2. Update the API client to use these error classes:

```tsx
// src/services/api/client.ts
import { ApiError, NetworkError, TimeoutError } from './errors';

// Inside the fetch method
try {
  const response = await fetch(url, options);
  
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch (e) {
      errorData = { message: 'Unknown error' };
    }
    
    throw new ApiError(
      errorData.message || `API error with status ${response.status}`,
      response.status,
      errorData
    );
  }
  
  return await response.json();
} catch (error) {
  if (error instanceof ApiError) {
    throw error;
  }
  
  if (error.name === 'AbortError') {
    throw new TimeoutError();
  }
  
  throw new NetworkError(error.message);
}
```

3. Add retry logic for transient errors:

```tsx
// src/services/api/client.ts
async function fetchWithRetry(url: string, options: RequestInit, retries = 3, delay = 300) {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (retries === 0 || error instanceof ApiError) {
      throw error;
    }
    
    // Only retry on network errors
    if (error instanceof NetworkError) {
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 2);
    }
    
    throw error;
  }
}
```

## Phase 2: Performance Optimizations (Priority: Medium)

### 1. Implement React.memo and useCallback

Use React.memo to prevent unnecessary re-renders of components and useCallback to memoize functions.

#### Implementation Plan:

1. Wrap appropriate components with React.memo:

```tsx
// Before
export default MyComponent;

// After
export default React.memo(MyComponent);
```

2. Use useCallback for event handlers and functions passed as props:

```tsx
// Before
const handleClick = () => {
  // handle click
};

// After
const handleClick = useCallback(() => {
  // handle click
}, [/* dependencies */]);
```

3. Apply to key components first:
   - ContentList
   - ContentViewer
   - SectionView
   - SceneView

### 2. Implement useMemo for Expensive Calculations

Use useMemo to memoize expensive calculations and prevent them from being re-computed on every render.

#### Implementation Plan:

1. Identify expensive calculations in components:

```tsx
// Before
const filteredItems = items.filter(item => item.status === status);

// After
const filteredItems = useMemo(() => {
  return items.filter(item => item.status === status);
}, [items, status]);
```

2. Apply to components with complex data transformations:
   - ContentList (filtering/sorting)
   - ContentViewer (data processing)
   - SectionView (scene filtering)

### 3. Implement Code Splitting

Use React.lazy and Suspense to split the code into smaller chunks that are loaded on demand.

#### Implementation Plan:

1. Set up React.lazy for route-based code splitting:

```tsx
// src/app/routes.tsx
import React, { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const ContentList = lazy(() => import('@/features/content/components/ContentList'));
const ContentForm = lazy(() => import('@/features/content/components/ContentForm'));
const ContentViewer = lazy(() => import('@/features/content/components/ContentViewer'));

const AppRoutes = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <Routes>
      <Route path="/" element={<ContentList />} />
      <Route path="/content/new" element={<ContentForm />} />
      <Route path="/content/:id" element={<ContentViewer />} />
    </Routes>
  </Suspense>
);

export default AppRoutes;
```

2. Create a LoadingSpinner component:

```tsx
// src/components/common/LoadingSpinner.tsx
import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner: React.FC = () => (
  <div className="loading-spinner-container">
    <div className="loading-spinner"></div>
  </div>
);

export default LoadingSpinner;
```

## Phase 3: Design System Foundation (Priority: Medium)

### 1. Create Basic UI Components

Create reusable UI components that can be used throughout the application.

#### Implementation Plan:

1. Create a Button component:

```tsx
// src/components/ui/Button.tsx
import React from 'react';
import './Button.css';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success';
type ButtonSize = 'small' | 'medium' | 'large';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  return (
    <button
      className={`btn btn-${variant} btn-${size} ${isLoading ? 'btn-loading' : ''} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <span className="btn-spinner"></span>}
      {icon && <span className="btn-icon">{icon}</span>}
      {children}
    </button>
  );
};

export default Button;
```

2. Create a Card component:

```tsx
// src/components/ui/Card.tsx
import React from 'react';
import './Card.css';

interface CardProps {
  title?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ title, children, footer, className = '' }) => {
  return (
    <div className={`card ${className}`}>
      {title && <div className="card-header">{title}</div>}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
};

export default Card;
```

3. Create a Form components:

```tsx
// src/components/ui/FormGroup.tsx
import React from 'react';
import './FormGroup.css';

interface FormGroupProps {
  label?: string;
  htmlFor?: string;
  error?: string;
  children: React.ReactNode;
}

const FormGroup: React.FC<FormGroupProps> = ({ label, htmlFor, error, children }) => {
  return (
    <div className={`form-group ${error ? 'has-error' : ''}`}>
      {label && <label htmlFor={htmlFor}>{label}</label>}
      {children}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};

export default FormGroup;
```

### 2. Create a Theme System

Create a theme system that can be used to customize the look and feel of the application.

#### Implementation Plan:

1. Create a theme file:

```tsx
// src/styles/theme.ts
export const theme = {
  colors: {
    primary: '#007bff',
    secondary: '#6c757d',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    light: '#f8f9fa',
    dark: '#343a40',
    white: '#ffffff',
    black: '#000000',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  fontSizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.25rem',
    xl: '1.5rem',
  },
  breakpoints: {
    xs: '0px',
    sm: '576px',
    md: '768px',
    lg: '992px',
    xl: '1200px',
  },
};

export type Theme = typeof theme;
```

2. Create CSS variables from the theme:

```css
/* src/styles/variables.css */
:root {
  /* Colors */
  --color-primary: #007bff;
  --color-secondary: #6c757d;
  --color-success: #28a745;
  --color-danger: #dc3545;
  --color-warning: #ffc107;
  --color-info: #17a2b8;
  --color-light: #f8f9fa;
  --color-dark: #343a40;
  --color-white: #ffffff;
  --color-black: #000000;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Font Sizes */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  
  /* Border Radius */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.5rem;
  --border-radius-lg: 1rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

## Phase 4: Automated Testing (Priority: Low)

### 1. Set Up Testing Framework

Set up Jest and React Testing Library for unit and integration testing.

#### Implementation Plan:

1. Install testing dependencies:

```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
```

2. Configure Jest in package.json:

```json
{
  "jest": {
    "testEnvironment": "jsdom",
    "setupFilesAfterEnv": [
      "<rootDir>/src/setupTests.ts"
    ],
    "moduleNameMapper": {
      "^@/(.*)$": "<rootDir>/src/$1",
      "\\.(css|less|scss|sass)$": "identity-obj-proxy"
    }
  }
}
```

3. Create setupTests.ts:

```tsx
// src/setupTests.ts
import '@testing-library/jest-dom';
```

### 2. Write Tests for Key Components

Write unit tests for key components to ensure they work as expected.

#### Implementation Plan:

1. Test the Button component:

```tsx
// src/components/ui/Button.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from './Button';

describe('Button', () => {
  test('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  test('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('is disabled when isLoading is true', () => {
    render(<Button isLoading>Click me</Button>);
    expect(screen.getByText('Click me').closest('button')).toBeDisabled();
  });
});
```

2. Test the ContentList component:

```tsx
// src/features/content/components/ContentList.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import contentReducer from '@/store/slices/contentSlice';
import ContentList from './ContentList';

const mockStore = configureStore({
  reducer: {
    content: contentReducer,
  },
  preloadedState: {
    content: {
      items: [
        {
          id: '1',
          title: 'Test Content',
          description: 'Test Description',
          status: 'completed',
          created_at: '2023-01-01T00:00:00Z',
        },
      ],
      loading: false,
      error: null,
    },
  },
});

describe('ContentList', () => {
  test('renders content items', () => {
    render(
      <Provider store={mockStore}>
        <BrowserRouter>
          <ContentList />
        </BrowserRouter>
      </Provider>
    );
    
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});
```

## Implementation Timeline

### Week 1: Error Handling
- Day 1-2: Implement ErrorBoundary component and apply to key components
- Day 3-4: Enhance API error handling with custom error classes
- Day 5: Add retry logic for transient errors

### Week 2: Performance Optimizations
- Day 1-2: Apply React.memo and useCallback to key components
- Day 3-4: Implement useMemo for expensive calculations
- Day 5: Set up code splitting with React.lazy and Suspense

### Week 3: Design System Foundation
- Day 1-2: Create basic UI components (Button, Card, FormGroup)
- Day 3-4: Create theme system with CSS variables
- Day 5: Apply UI components to one feature as a proof of concept

### Week 4: Automated Testing
- Day 1-2: Set up testing framework
- Day 3-5: Write tests for key components and utilities

## Conclusion

This implementation plan provides a roadmap for further improving the frontend architecture. The phases are prioritized based on their impact and complexity, with error handling being the highest priority due to its immediate benefit to user experience.

Each phase builds upon the previous ones, creating a more robust, performant, and maintainable codebase. The timeline is flexible and can be adjusted based on team capacity and project priorities.
