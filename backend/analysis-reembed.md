# Novel Analysis and Embeddings Pipeline

## Overview
This document details the comprehensive pipeline for analyzing novels at multiple granularity levels, embedding them for semantic retrieval, and enabling intelligent interactions with the content. The system is designed to handle major revisions while maintaining coherence and enabling context-aware discussions at the novel, chapter, and paragraph levels.

## System Architecture

### Core Components
1. **FastAPI Backend** - Provides REST endpoints for processing novels, chapters, and paragraphs
2. **NovelProcessor** - Main processing pipeline for text analysis and embedding generation
3. **MilvusNovelStore** - Vector database for efficient storage and retrieval of embeddings
4. **Analysis Modules** - Specialized modules for plot structure, character arcs, and narrative analysis

### Processing Granularity
- **Novel-level** - Complete processing of the full text with plot structure analysis
- **Chapter-level** - Context-aware processing with surrounding narrative elements
- **Paragraph-level** - Fine-grained analysis with local and global context

## Processing Pipeline

### 1. Text Preprocessing
```python
def _preprocess_novel(self, content: str) -> List[Dict[str, Any]]:
    # Clean text (remove formatting artifacts, normalize whitespace)
    cleaned_text = self._clean_text(content)
    
    # Split into semantic chunks
    raw_chunks = self.text_splitter.split_text(cleaned_text)
    
    # Process each chunk
    processed_chunks = []
    for i, chunk in enumerate(raw_chunks):
        doc = self.nlp(chunk)
        processed_chunks.append({
            "id": f"chunk_{i}",
            "content": chunk,
            "entities": self._extract_entities(doc),
            "semantic_type": self._classify_chunk(doc),
            "position": i
        })
    
    return processed_chunks
```

#### Chunk Classification Algorithm
The system classifies each chunk into one of several semantic types:
- **Exposition** - Background information or scene setting
- **Dialogue** - Character conversations
- **Action** - Plot advancement through events
- **Internal** - Character thoughts or reflections
- **Transition** - Scene or time shifts

Classification uses a combination of:
- Dialogue-to-narrative ratio
- Tense and point-of-view analysis
- Entity density and types
- Temporal markers
- Linguistic features (sentence length, complexity)

### 2. Embedding Generation

```python
async def _generate_novel_embeddings(self, novel: Novel, chunks: List[Dict]) -> Dict[str, Any]:
    # Generate chunk embeddings with contextual awareness
    chunk_embeddings = []
    for i, chunk in enumerate(chunks):
        # Get surrounding context
        context_before = chunks[i-1]["content"] if i > 0 else ""
        context_after = chunks[i+1]["content"] if i < len(chunks)-1 else ""
        
        # Generate embedding with context window
        embedding = await self._embed_with_context(
            chunk["content"],
            context_before,
            context_after
        )
        
        chunk_embeddings.append({
            "id": chunk["id"],
            "content": chunk["content"],
            "embedding": embedding,
            "semantic_type": chunk["semantic_type"],
            "entities": chunk["entities"],
            "position": chunk["position"]
        })
    
    # Generate chapter embeddings
    chapter_embeddings = []
    for chapter in novel.chapters:
        # Get chapter content
        chapter_content = chapter["content"]
        
        # Special embedding that captures narrative structure
        chapter_embedding = await self._embed_chapter(
            chapter_content,
            chapter["title"]
        )
        
        chapter_embeddings.append({
            "id": chapter["id"],
            "title": chapter["title"],
            "embedding": chapter_embedding,
            "position": chapter["position"],
            "summary": await self._generate_chapter_summary(chapter_content)
        })
    
    # Generate plot point embeddings
    plot_embeddings = await self._embed_plot_points(chunks)
    
    return {
        "chunks": chunk_embeddings,
        "chapters": chapter_embeddings,
        "plot": plot_embeddings
    }
```

#### Embedding Strategies
The system uses different embedding strategies for different content types:

1. **Chunk Embeddings**
   - Include surrounding context for continuity
   - Optimized for semantic search and similarity
   - Dimension: 768

2. **Chapter Embeddings**
   - Capture high-level narrative structure
   - Include title and position information
   - Optimized for story flow understanding
   - Dimension: 768

3. **Plot Point Embeddings**
   - Specialized for narrative elements
   - Enhanced with character and theme information
   - Optimized for plot analysis
   - Dimension: 768

### 3. Plot Structure Analysis

```python
async def _analyze_plot_structure(self, chunks: List[Dict]) -> Dict[str, Any]:
    # Identify major plot points using narrative tension analysis
    plot_points = self._identify_plot_points(chunks)
    
    # Track character arcs using entity-based state tracking
    character_arcs = self._track_character_arcs(chunks)
    
    # Identify narrative threads using thematic clustering
    narrative_threads = self._identify_narrative_threads(chunks)
    
    # Analyze story structure
    story_structure = self._analyze_story_structure(
        plot_points,
        chunks
    )
    
    return {
        "plot_points": plot_points,
        "character_arcs": character_arcs,
        "narrative_threads": narrative_threads,
        "story_structure": story_structure,
        "summary": self._generate_plot_summary(
            plot_points, 
            character_arcs, 
            narrative_threads
        )
    }
```

#### Plot Point Identification Algorithm
The system identifies key plot points through:
1. **Narrative Tension Analysis**
   - Measures emotional intensity using sentiment analysis
   - Tracks linguistic markers of tension (e.g., shorter sentences, intensifiers)
   - Identifies climactic moments through keyword and pattern recognition

2. **Character State Changes**
   - Tracks major changes in character states or goals
   - Identifies pivotal decisions or revelations
   - Monitors relationship dynamics

3. **Scene Structure Analysis**
   - Identifies scene boundaries
   - Measures scene importance through entity density
   - Analyzes scene-level tension arcs

#### Character Arc Tracking
The system tracks character development through:
1. **Entity Extraction and Coreference Resolution**
   - Identifies character mentions including pronouns
   - Links mentions to character entities

2. **Character State Tracking**
   - Monitors emotional states
   - Tracks goal changes
   - Identifies key relationships and their evolution

3. **Character Network Analysis**
   - Maps character interactions
   - Quantifies relationship strength
   - Identifies relationship changes

#### Narrative Thread Identification
The system identifies and tracks narrative threads through:
1. **Thematic Clustering**
   - Groups related plot elements by theme
   - Identifies recurrent motifs

2. **Continuity Analysis**
   - Tracks thread mentions across chapters
   - Identifies unresolved threads

3. **Importance Weighting**
   - Ranks threads by narrative significance
   - Measures thread development

### 4. Milvus Storage Implementation

```python
async def _store_chunks(self, novel_id: str, version_id: str, chunks: List[Dict]):
    """Store chunk embeddings in Milvus"""
    # Prepare data for insertion
    ids = [chunk["id"] for chunk in chunks]
    content = [chunk["content"] for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    chapter_ids = [chunk.get("chapter_id", "") for chunk in chunks]
    positions = [chunk["position"] for chunk in chunks]
    semantic_types = [chunk["semantic_type"] for chunk in chunks]
    entities = [json.dumps(chunk["entities"]) for chunk in chunks]
    timestamps = [int(time.time()) for _ in chunks]
    
    # Insert into Milvus
    self.chunks.insert([
        ids,                     # id
        content,                 # content
        embeddings,              # embedding
        [novel_id] * len(chunks),  # novel_id
        chapter_ids,             # chapter_id
        [version_id] * len(chunks), # version_id
        positions,               # position
        semantic_types,          # semantic_type
        entities,                # entities
        timestamps               # timestamp
    ])
    
    # Create index if not exists
    if not self.chunks.has_index():
        index_params = {
            "metric_type": "L2",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 500}
        }
        self.chunks.create_index("embedding", index_params)
```

#### Query Optimization Strategies
For efficient retrieval, the system uses:

1. **Two-stage Retrieval**
   - First-pass retrieval using approximate search
   - Reranking of initial results with more precise metrics

2. **Context-aware Search**
   - Uses query expansion based on narrative context
   - Incorporates plot position in search relevance

3. **Hybrid Search**
   - Combines vector similarity with metadata filtering
   - Weights results by narrative importance

```python
async def search_similar_passages(
    self,
    query_text: str,
    novel_id: str,
    version_id: str,
    context: Optional[Dict] = None,
    limit: int = 10
) -> List[Dict]:
    """Search for similar passages with context awareness"""
    # Generate query embedding
    query_embedding = await self._embed_text(query_text)
    
    # Set up search parameters
    search_params = {
        "metric_type": "L2",
        "params": {"ef": 100}
    }
    
    # Build filter expression
    expr = f'novel_id == "{novel_id}" && version_id == "{version_id}"'
    
    # Add context filters if provided
    if context and "chapter_id" in context:
        expr += f' && chapter_id == "{context["chapter_id"]}"'
    
    # Execute search
    results = self.chunks.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=limit,
        expr=expr
    )
    
    # Format and return results
    formatted_results = self._format_search_results(results)
    
    # If context provided, rerank by narrative relevance
    if context and "narrative_position" in context:
        formatted_results = self._rerank_by_narrative_relevance(
            formatted_results,
            context["narrative_position"]
        )
    
    return formatted_results
```

## Version Control Implementation

The system maintains coherence across revisions through:

### 1. Revision Tracking
Each processing generates a unique version ID based on content hash:

```python
def _generate_version_id(self, novel: Novel) -> str:
    """Generate deterministic version ID based on content"""
    content_hash = hashlib.sha256(novel.content.encode()).hexdigest()
    timestamp = int(time.time())
    return f"{novel.id}_{content_hash[:10]}_{timestamp}"
```

### 2. Delta Analysis
When handling revisions, the system identifies what has changed:

```python
async def analyze_revision_changes(
    self,
    novel_id: str,
    previous_version: str,
    current_version: str
) -> Dict[str, Any]:
    """Analyze changes between versions"""
    # Get previous version data
    previous_data = await self._get_version_data(novel_id, previous_version)
    
    # Get current version data
    current_data = await self._get_version_data(novel_id, current_version)
    
    # Compare chapters
    chapter_changes = self._compare_chapters(
        previous_data["chapters"],
        current_data["chapters"]
    )
    
    # Compare plot structure
    plot_changes = self._compare_plot_structure(
        previous_data["plot_structure"],
        current_data["plot_structure"]
    )
    
    # Generate coherence impacts
    coherence_impacts = self._analyze_coherence_impacts(
        chapter_changes,
        plot_changes
    )
    
    return {
        "chapter_changes": chapter_changes,
        "plot_changes": plot_changes,
        "coherence_impacts": coherence_impacts,
        "suggested_revisions": self._generate_revision_suggestions(coherence_impacts)
    }
```

### 3. Coherence Maintenance
The system identifies potential coherence issues after revisions:

```python
def _analyze_coherence_impacts(
    self,
    chapter_changes: Dict[str, Any],
    plot_changes: Dict[str, Any]
) -> List[Dict]:
    """Analyze coherence impacts from changes"""
    impacts = []
    
    # Check for character continuity issues
    character_issues = self._check_character_continuity(
        chapter_changes["reordered"],
        chapter_changes["modified"]
    )
    impacts.extend(character_issues)
    
    # Check for plot thread disruptions
    thread_issues = self._check_plot_thread_continuity(
        chapter_changes["reordered"],
        chapter_changes["modified"],
        plot_changes["modified_threads"]
    )
    impacts.extend(thread_issues)
    
    # Check for logical inconsistencies
    logic_issues = self._check_logical_consistency(
        chapter_changes["modified"],
        plot_changes["modified_plot_points"]
    )
    impacts.extend(logic_issues)
    
    return impacts
```

## Interactive Features

### 1. Chapter-Level Interaction

```python
async def prepare_chapter_context(
    self,
    chapter_id: str,
    novel_id: str,
    version_id: str
) -> Dict[str, Any]:
    """Prepare rich context for chapter-level interaction"""
    # Get chapter data
    chapter = await self.vector_store.get_chapter(
        chapter_id,
        novel_id,
        version_id
    )
    
    # Get narrative position
    narrative_position = await self._get_narrative_position(
        chapter,
        novel_id,
        version_id
    )
    
    # Get character states at this point
    character_states = await self._get_character_states_at_point(
        chapter,
        novel_id,
        version_id
    )
    
    # Get active plot threads
    active_threads = await self._get_active_plot_threads(
        chapter,
        novel_id,
        version_id
    )
    
    return {
        "chapter": chapter,
        "narrative_position": narrative_position,
        "character_states": character_states,
        "active_threads": active_threads
    }
```

### 2. Paragraph-Level Analysis

```python
async def analyze_paragraph(
    self,
    paragraph: Paragraph,
    novel_id: str,
    version_id: str,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """Analyze a paragraph with surrounding context"""
    # Get chapter context
    chapter_context = await self.vector_store.get_chapter_context(
        paragraph.chapter_id,
        novel_id,
        version_id
    )
    
    # Get paragraph context
    surrounding_text = await self._get_surrounding_paragraphs(
        paragraph,
        novel_id,
        version_id
    )
    
    # Generate analysis based on type
    if analysis_type == "style":
        analysis = await self._analyze_paragraph_style(
            paragraph.content,
            surrounding_text
        )
    elif analysis_type == "narrative":
        analysis = await self._analyze_paragraph_narrative_role(
            paragraph.content,
            chapter_context,
            surrounding_text
        )
    elif analysis_type == "revision":
        analysis = await self._generate_paragraph_revision_suggestions(
            paragraph.content,
            chapter_context,
            surrounding_text
        )
    else:  # comprehensive
        analysis = await self._comprehensive_paragraph_analysis(
            paragraph.content,
            chapter_context,
            surrounding_text
        )
    
    return analysis
```

## Advanced Analysis Algorithms

### 1. Narrative Structure Analysis

The system identifies story structure using the following algorithm:

```python
def _analyze_story_structure(self, plot_points: List[Dict], chunks: List[Dict]) -> Dict[str, Any]:
    """Analyze overall story structure"""
    # Map tension across story
    tension_map = self._map_narrative_tension(chunks)
    
    # Identify structural elements
    inciting_incident = self._identify_inciting_incident(plot_points, tension_map)
    rising_action_points = self._identify_rising_action(plot_points, tension_map)
    climax = self._identify_climax(plot_points, tension_map)
    falling_action_points = self._identify_falling_action(plot_points, tension_map, climax)
    resolution = self._identify_resolution(plot_points, tension_map, climax)
    
    # Identify structural patterns
    structure_pattern = self._identify_structure_pattern([
        inciting_incident,
        rising_action_points,
        climax,
        falling_action_points,
        resolution
    ])
    
    return {
        "structure_pattern": structure_pattern,
        "key_points": {
            "inciting_incident": inciting_incident,
            "rising_action": rising_action_points,
            "climax": climax,
            "falling_action": falling_action_points,
            "resolution": resolution
        },
        "tension_map": tension_map
    }
```

The tension mapping algorithm:

```python
def _map_narrative_tension(self, chunks: List[Dict]) -> List[float]:
    """Map narrative tension throughout the story"""
    tension_scores = []
    
    for chunk in chunks:
        # Calculate base tension from sentiment
        sentiment_score = self._calculate_sentiment(chunk["content"])
        
        # Adjust for dialogue intensity
        dialogue_factor = self._calculate_dialogue_intensity(chunk["content"])
        
        # Adjust for pacing (sentence length, complexity)
        pacing_factor = self._calculate_pacing_factor(chunk["content"])
        
        # Adjust for presence of conflict markers
        conflict_factor = self._calculate_conflict_factor(chunk["content"], chunk["entities"])
        
        # Combine factors with appropriate weights
        tension_score = (
            (sentiment_score * 0.4) +
            (dialogue_factor * 0.2) +
            (pacing_factor * 0.2) +
            (conflict_factor * 0.2)
        )
        
        tension_scores.append(tension_score)
    
    # Smooth the curve
    smoothed_tension = self._smooth_curve(tension_scores)
    
    return smoothed_tension
```

### 2. Character Development Tracking

```python
def _track_character_arcs(self, chunks: List[Dict]) -> Dict[str, Any]:
    """Track character development arcs"""
    # Extract all characters
    all_characters = self._extract_all_characters(chunks)
    
    character_arcs = {}
    for character in all_characters:
        # Skip minor characters
        if not self._is_major_character(character, chunks):
            continue
        
        # Track character mentions
        mentions = self._track_character_mentions(character, chunks)
        
        # Track emotional states
        emotional_states = self._track_emotional_states(character, chunks)
        
        # Track goals and motivations
        goals = self._track_character_goals(character, chunks)
        
        # Track relationships
        relationships = self._track_character_relationships(character, chunks)
        
        # Identify key development points
        development_points = self._identify_character_development_points(
            character,
            mentions,
            emotional_states,
            goals
        )
        
        character_arcs[character] = {
            "mentions": mentions,
            "emotional_arc": emotional_states,
            "goal_evolution": goals,
            "relationships": relationships,
            "development_points": development_points,
            "arc_type": self._classify_character_arc(development_points, emotional_states)
        }
    
    return character_arcs
```

## Performance Optimization

### 1. Batch Processing

The system uses batch processing for embedding generation:

```python
async def _embed_chunks_batch(self, chunks: List[Dict], batch_size: int = 8) -> List[Dict]:
    """Process chunks in batches for efficiency"""
    results = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        # Process batch in parallel
        batch_texts = [chunk["content"] for chunk in batch]
        batch_embeddings = await self._batch_embed(batch_texts)
        
        # Combine results
        for j, chunk in enumerate(batch):
            chunk_copy = chunk.copy()
            chunk_copy["embedding"] = batch_embeddings[j]
            results.append(chunk_copy)
    
    return results
```

### 2. Incremental Processing

For revisions, the system only processes changed content:

```python
async def process_revision(
    self,
    novel_id: str,
    previous_version: str,
    modified_chapters: List[str],
    full_novel: Novel
) -> Dict[str, Any]:
    """Process only modified chapters for efficiency"""
    # Get previous version data
    previous_data = await self.vector_store.get_version_data(
        novel_id,
        previous_version
    )
    
    # Generate new version ID
    new_version = self._generate_version_id(full_novel)
    
    # Process modified chapters
    modified_chapter_data = await self._process_chapters(
        [c for c in full_novel.chapters if c["id"] in modified_chapters],
        full_novel
    )
    
    # Copy unmodified chapter data
    unmodified_chapter_data = [
        c for c in previous_data["chapters"] 
        if c["id"] not in modified_chapters
    ]
    
    # Combine data
    all_chapter_data = modified_chapter_data + unmodified_chapter_data
    
    # Update plot structure based on changes
    new_plot_structure = await self._update_plot_structure(
        previous_data["plot_structure"],
        modified_chapter_data,
        full_novel
    )
    
    # Store updated data
    await self.vector_store.store_revision(
        novel_id,
        new_version,
        {
            "chunks": modified_chapter_data["chunks"],
            "chapters": all_chapter_data,
            "plot_structure": new_plot_structure
        }
    )
    
    return {
        "version_id": new_version,
        "modified_chapters": modified_chapters,
        "coherence_analysis": await self._analyze_revision_coherence(
            previous_data,
            {
                "chapters": all_chapter_data,
                "plot_structure": new_plot_structure
            },
            modified_chapters
        )
    }
```

## Error Handling and Edge Cases

The system handles several edge cases:

1. **Empty or Very Short Novels**
   - Minimum content thresholds
   - Simplified analysis for very short works

2. **Unusual Narrative Structures**
   - Special handling for non-linear narratives
   - Support for multiple POVs and narrative frames

3. **Heavy Dialogue or Experimental Styles**
   - Adaptive chunking based on content style
   - Special processing for dialogue-heavy sections

```python
def _adapt_processing_to_style(self, novel: Novel) -> Dict[str, Any]:
    """Adapt processing strategy based on novel style"""
    # Analyze style characteristics
    style_analysis = self._analyze_novel_style(novel.content)
    
    processing_params = {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "embedding_strategy": "standard",
        "analysis_depth": "standard"
    }
    
    # Adjust for dialogue-heavy content
    if style_analysis["dialogue_ratio"] > 0.7:
        processing_params["chunk_size"] = 1500
        processing_params["chunk_overlap"] = 300
        processing_params["embedding_strategy"] = "dialogue_optimized"
    
    # Adjust for experimental or stream-of-consciousness
    if style_analysis["sentence_complexity"] > 0.8:
        processing_params["chunk_size"] = 800
        processing_params["embedding_strategy"] = "semantic_boundary"
        
    # Adjust for very short works
    if len(novel.content) < 10000:
        processing_params["chunk_size"] = 500
        processing_params["chunk_overlap"] = 100
        processing_params["analysis_depth"] = "simplified"
    
    return processing_params
```

## Conclusion

This novel analysis and embedding pipeline provides a comprehensive framework for:

1. Processing novels at different granularity levels
2. Generating semantically rich embeddings
3. Analyzing narrative structure, plot, and characters
4. Maintaining coherence across revisions
5. Enabling intelligent interaction with the text

The system balances deep literary analysis with efficient implementation, making it suitable for both individual authors and larger-scale applications in literary analysis, editing, and AI-assisted writing.