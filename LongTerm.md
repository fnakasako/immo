# Immo:

## Overview

Immo is an AI-powered platform that empowers users to generate and refine the books. Initially focused on literature & novel generation, the platform aims to evolve into a comprehensive creative assitant that leverage multi-modal output/ML techniques, LLM research, agentic AI, RAG, and multi-model techniues.

## Long-term vision:

- **Empower Creativity:** Enable users to generate novels, jounalistic pieces, scripts, etc. 
- **Integrate Advanced AI Techniues:** Incorporate unique LLM/AI research,  agentic AI behavior (models autonomously handling narrative aspects), and RAG to pull in external knowledge where needed. 
- **Support Multi-modal Interactions:** Allow users to enhance generation through images, audio inputs, etc.
- **Iterative, User-driven Refinement:** Learn from user inputs to continuously improve story generation quality, personalizing creative output to user tastes
- **Scalability and Extensibility:** Mantain a modular codebase to easily integrate new services and performance-critical modules.

## Medium-to-Long Term Goals

- **Advanced Story Forms:** Expand beyond novels to support journalism, scripts, etc. 
- **Agentic AI & autonomous Modules:** Implement autonomous agents for character development, world-building, and dialogue generation.
- **RAG and Fine-tuning:** Integration retrieval-augmented generation and special fine-tuning for genre-specific storytelling.
- **Multi-modal and Collaborative Features:** Enable users to provide images and audio inputs, incorporate an AI chat assistant, and offer collaborative editing.
- **Rust-powered High-Performance Modules:** Over time, offload performance-critical tasks (like real-time streaming) to Rust microservices.
- **Community-Driven Refinement:** Implement robust feedback loops and analytics to drive continuous research and iterative improvement.


## Tech Stack

- **Frontend:** React, Typescript, Vite.
- **Backend:** FastAPI, MongoDB or SQL?

creativity-booster/
├── README.md
├── LICENSE.md
├── docs/
│ ├── architecture.md # High-level system architecture
│ ├── dev_guidelines.md # Coding standards & best practices
│ └── roadmap.md # Project evolution roadmap & future features
├── frontend/ # React + TypeScript web client
│ ├── package.json
│ ├── public/
│ ├── src/
│ │ ├── components/ # Reusable UI components
│ │ ├── pages/ # View components/pages
│ │ ├── services/ # API service clients
│ │ ├── store/ # State management (e.g., Redux)
│ │ ├── App.tsx # Main app component
│ │ └── index.tsx # Application entry point
│ └── tests/ # Frontend tests (unit & integration)
├── backend/ # FastAPI backend application
│ ├── Dockerfile
│ ├── requirements.txt
│ ├── .env.example
│ ├── app/
│ │ ├── init.py
│ │ ├── main.py # API entry-point
│ │ ├── config/ # Project configuration & settings
│ │ │ ├── init.py
│ │ │ └── settings.py
│ │ ├── api/ # API Versioning & Routes
│ │ │ ├── init.py
│ │ │ └── routes/
│ │ │ ├── init.py
│ │ │ ├── novel.py # Endpoints for novel generation
│ │ │ ├── auth.py # (Future) Authentication routes
│ │ │ └── chatbot.py # (Future) AI-chatbot assistant
│ │ ├── models/ # Pydantic models & ORM model definitions
│ │ │ ├── init.py
│ │ │ ├── novel.py
│ │ │ └── user.py
│ │ ├── services/ # Business logic & AI integrations
│ │ │ ├── init.py
│ │ │ ├── ai_integration.py # AI prompt handling & external service calls
│ │ │ ├── storage.py # Future: Data storage & caching helpers
│ │ │ ├── agentic.py # (Future) Agentic AI controllers
│ │ │ └── rag.py # (Future) Retrieval-Augmented Generation
│ │ ├── controllers/ # High-level router logic separating business concerns
│ │ │ ├── init.py
│ │ │ └── novel_controller.py
│ │ ├── tasks/ # Background tasks (e.g., Celery tasks)
│ │ │ ├── init.py
│ │ │ ├── background_tasks.py
│ │ │ └── multi_modal_processor.py # (Future) Streaming/multi-modal processing
│ │ ├── middleware/ # Custom middleware (CORS, error handlers, logging)
│ │ │ ├── init.py
│ │ │ ├── cors.py
│ │ │ └── error_handler.py
│ │ └── utils/ # Utility functions, logging, and helper libraries
│ │ ├── init.py
│ │ ├── logging.py
│ │ └── security.py
│ └── tests/ # Backend tests (unit, integration, end-to-end)
│ ├── init.py
│ ├── test_novel_api.py
│ └── test_services.py
├── rust_services/ # Future performance-critical microservices (in Rust)
│ ├── novel_streaming/ # Example: Real-time streaming, heavy computations
│ │ ├── Cargo.toml
│ │ └── src/
│ │ └── lib.rs
│ └── README.md # Documentation for Rust modules
└── scripts/ # Utility scripts for deployment, testing, etc.
├── deployment.sh # Deployment automation script
├── setup.sh # Local development setup automation
└── run_tests.sh # Automated testing commands