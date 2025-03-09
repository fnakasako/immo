// src/components/ContentForm.tsx
import React, { useState, ChangeEvent, FormEvent } from 'react';
import { ContentGenerationRequest, StyleOption } from '../../types';
import '../styles/ContentForm.css';

interface ContentFormProps {
  onSubmit: (data: ContentGenerationRequest) => void;
  isSubmitting: boolean;
}

const styleOptions: StyleOption[] = [
  { value: 'literary', label: 'Literary Fiction' },
  { value: 'thriller', label: 'Thriller' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'sci-fi', label: 'Science Fiction' },
  { value: 'historical', label: 'Historical Fiction' }
];

const ContentForm: React.FC<ContentFormProps> = ({ onSubmit, isSubmitting }) => {
  const [formData, setFormData] = useState<ContentGenerationRequest>({
    description: '',
    style: 'literary',
    sections_count: 5
  });

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'sections_count' ? parseInt(value) : value
    }));
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="content-form">
      <h2>Create New Content</h2>
      
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
          disabled={isSubmitting}
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
          disabled={isSubmitting}
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
          disabled={isSubmitting}
        />
      </div>
      
      <button 
        type="submit" 
        className="submit-button"
        disabled={isSubmitting || !formData.description.trim()}
      >
        {isSubmitting ? 'Generating...' : 'Generate Content'}
      </button>
    </form>
  );
};

export default ContentForm;
