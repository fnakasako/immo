// Import React and hooks
import { useState } from 'react';

// Define TypeScript interfaces
interface Chapter {
  title: string;
  content: string;
}

function App() {
  // State management using useState hook
  const [description, setDescription] = useState('');
  const [numChapters, setNumChapters] = useState(3);
  const [model, setModel] = useState('claude-3.5');
  const [output, setOutput] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(false);

  // Async function triggered by form submission
  const generateNovel = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // HTTP POST request to backend
      const response = await fetch('http://localhost:3001/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, chapters: numChapters, model })
      });
      
      // Update state with API response
      const data = await response.json();
      setOutput(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // JSX markup for UI rendering
  return (
    <div className="App">
      <form onSubmit={generateNovel}>
        <textarea 
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter story description..."
        />
        
        <input
          type="number"
          value={numChapters}
          onChange={(e) => setNumChapters(Number(e.target.value))}
          min="1"
          max="10"
        />
        
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="claude-3.5">Claude 3.5</option>
          <option value="gpt-4">GPT-4</option>
        </select>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Generating...' : 'Generate Novel'}
        </button>
      </form>
      
      <div className="output">
        {output.map((chapter, index) => (
          <div key={index}>
            <h3>{chapter.title}</h3>
            <p>{chapter.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}