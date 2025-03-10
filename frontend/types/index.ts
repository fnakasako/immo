export enum GenerationStatus {
    PENDING = 'pending',
    PROCESSING_OUTLINE = 'processing_outline',
    PROCESSING_SECTIONS = 'processing_sections',
    COMPLETED = 'completed',
    PARTIALLY_COMPLETED = 'partially_completed',
    FAILED = 'failed'
}

export enum SectionStatus {
    PENDING = 'pending',
    GENERATING_SCENES = 'generating_scenes',
    PROCESSING_SCENES = 'processing_scenes',
    COMPLETED = 'completed',
    FAILED = 'failed'
}

export enum SceneStatus {
    PENDING = 'pending',
    GENERATING = 'generating',
    COMPLETED = 'completed',
    FAILED = 'failed'
}

export interface ContentGenerationRequest {
    description: string;
    style?: string;
    sections_count?: number;
    model?: string;
}

export interface ContentGenerationResponse {
    id: string;
    title: string | null;
    outline: string | null;
    status: GenerationStatus;
    progress: number;
    error: string | null;
    created_at: string;
}

export interface SectionResponse {
    id: string;
    content_id: string;
    number: number;
    title: string;
    summary: string;
    status: SectionStatus;
    error: string | null;
}

export interface SectionListResponse {
    sections: SectionResponse[];
    total: number;
}

export interface SceneResponse {
    id: string;
    content_id: string;
    section_id: string;
    number: number;
    heading: string;
    setting: string;
    characters: string;
    key_events: string;
    emotional_tone: string;
    content: string | null;
    status: SceneStatus;
    error: string | null;
}

export interface SceneListResponse {
    scenes: SceneResponse[];
    total: number;
}

export interface StyleOption {
    value: string;
    label: string;
}
