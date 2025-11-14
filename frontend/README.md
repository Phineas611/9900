# Contract Analysis Dashboard

A comprehensive web application for analyzing legal contracts and identifying ambiguous language using AI-powered natural language processing.

## Overview

The Contract Analysis Dashboard is a React-based web application designed to help legal professionals, contract managers, and compliance teams analyze legal documents for ambiguous clauses and improve contract clarity. The system leverages advanced language models to provide detailed explanations of potentially problematic contract language.

## Features

### Dashboard
- **Overview Metrics**: Real-time statistics on contract processing
- **Recent Uploads**: Track and manage analyzed contracts
- **Quick Actions**: Fast access to common tasks and recent activities
- **Performance Analytics**: Monitor system performance and analysis trends

### Contract Repository
- **All Contracts**: Comprehensive view of all analyzed contracts with search and filtering
- **Trends & Patterns**: Visual analytics showing contract analysis trends over time
- **Recurring Phrases**: Identify commonly used ambiguous terms across contracts
- **Advanced Filtering**: Filter by contract type, status, and date ranges

### Sentence Analysis
- **Detailed Analysis**: In-depth examination of individual sentences
- **Ambiguity Detection**: AI-powered identification of unclear language
- **Plain-English Explanations**: Clear explanations of why phrases are ambiguous
- **Batch Processing**: Analyze multiple sentences simultaneously

### Evaluation Lab
- **Model Testing**: Compare different AI models and prompts
- **Custom Rubrics**: Define evaluation criteria for contract analysis
- **Batch Evaluation**: Test models on multiple sentences simultaneously
- **Performance Metrics**: Detailed analytics on model performance

### Prompt Lab
- **Prompt Engineering**: Test and optimize different prompt templates
- **Model Comparison**: Evaluate different language models side-by-side
- **Custom Prompts**: Create and test custom analysis prompts
- **File Processing**: Upload and analyze contract files in bulk

### Reports & Analytics
- **Model Performance**: Track explanation quality and accuracy metrics
- **Ambiguity Trends**: Monitor ambiguity rates over time
- **Contract Type Analysis**: Compare ambiguity across different contract types
- **Export Capabilities**: Generate comprehensive reports in multiple formats

## Technology Stack

### Frontend
- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe JavaScript development
- **React Router** - Client-side routing and navigation
- **Recharts** - Data visualization and charting library
- **CSS3** - Custom styling with modern CSS features

### Backend Integration
- **RESTful APIs** - Standardized API communication
- **JWT Authentication** - Secure user authentication
- **File Upload** - Support for multiple document formats
- **Real-time Updates** - WebSocket integration for live status updates

### AI/ML Integration
- **Language Models** - Integration with various LLMs
- **Ensemble Methods** - Combined model predictions for improved accuracy
- **Custom NLP Pipelines** - Specialized processing for legal text
- **Evaluation Framework** - Systematic model performance assessment

## Installation & Setup

### Prerequisites
- Node.js 16+ and npm/yarn
- Modern web browser with ES6+ support
- Backend API service (see backend documentation)

### Quick Start

1. **Clone the repository**
   git clone git@github.com:unsw-cse-comp99-3900/LegalContractAnalyzer_h18c_bread.git
   cd LegalContractAnalyzer_h18c_bread/frontend

2. **Install dependencies**
   npm install

3. **Start development server**
   npm run dev

4. **Open your browser**
   Navigate to http://localhost:5173

### Production Build
   npm run build

### Deployment
   The application is configured for easy deployment to Vercel. Simply run:
   npm run deploy

   The current front-end production version is deployed at: https://frontend-khaki-nine-49.vercel.app/
   The backend production version deployed at: https://legalcontractanalyzer-backend.onrender.com/docs
