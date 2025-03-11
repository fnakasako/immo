/**
 * Content Form Component
 * Form for creating new content
 */
import React, { useState, ChangeEvent, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useContent } from '../hooks/useContent';
import { ContentGenerationRequest, StyleOption } from '@/types';
import { generatePath } from '@/app/routes';
import './ContentForm.css';

// Style options for the form
const styleOptions: StyleOption[] = [
  { value: 'literary', label: 'Literary Fiction' },
  { value: 'thriller', label: 'Thriller' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'sci-fi', label: 'Science Fiction' },
  { value: 'historical', label: 'Historical Fiction' }
];

const ContentForm: React.FC = () => {
  const navigate = useNavigate();
  const { createContent, generateOutline, loading, error, clearError } = useContent();
  
  const [formData, setFormData] = useState<ContentGenerationRequest>({
    description: '',
    style: 'literary',
    sections_count: 5,
    model: 'default'
  });

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'sections_count' ? parseInt(value) : value
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    try {
      // Create the content
      const response = await createContent(formData).unwrap();
      
      // Generate the outline
      await generateOutline(response.id).unwrap();
      
      // Navigate to the content view page
      navigate(generatePath.contentView(response.id));
    } catch (err) {
      // Error handling is managed by the Redux slice
      console.error('Failed to create content:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="content-form">
      <h2>Create New Content</h2>
      <p className="help-text">
        Content generation is a step-by-step process. After creating the initial structure, 
        you'll be guided through generating the outline, sections, scenes, and prose.
      </p>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button type="button" onClick={clearError}>Dismiss</button>
        </div>
      )}
      
      <div className="form-group">
        <label htmlFor="description">Content Description</label>
        <textarea
          id="description"
          name="description"
          rows={4}
          value={formData.description}
          onChange={handleChange}
          placeholder="Describe your story, essay, article or other content..."
          required
          disabled={loading}
        />
        <p className="help-text">
          Provide a detailed description of what you want to generate.
          The more specific, the better the results.
        </p>
      </div>
      
      <div className="form-group">
        <label htmlFor="style">Writing Style</label>
        <select
          id="style"
          name="style"
          value={formData.style}
          onChange={handleChange}
          disabled={loading}
        >
          {styleOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="sections_count">Number of Sections</label>
        <input
          type="number"
          id="sections_count"
          name="sections_count"
          value={formData.sections_count}
          onChange={handleChange}
          min={2}
          max={10}
          disabled={loading}
        />
      </div>
      
      <button 
        type="submit" 
        className="submit-button"
        disabled={loading || !formData.description.trim()}
      >
        {loading ? 'Creating...' : 'Create Content Structure'}
      </button>
    </form>
  );
};

export default ContentForm;
