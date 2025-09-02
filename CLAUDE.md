# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Receiptor AI - Simplified Receipt Management System

### Development Commands

#### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python3 server.py
# OR
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Frontend (React)
```bash
cd frontend
bun install
bun start
```

#### Testing
```bash
# Test backend functionality
cd backend
python3 -c "import server; print('Backend OK')"

# Test frontend build
cd frontend
bun run build
```

## Architecture Overview

### Simplified Backend
- **FastAPI** with minimal dependencies (no database required)
- **In-memory storage** for development and testing
- **Mock AI processing** for receipt data extraction
- **CORS enabled** for frontend integration
- **File upload support** with multipart form handling

### Frontend Structure
- **React 19** with React Router v7
- **UI Framework**: shadcn/ui components built on Radix UI
- **Styling**: Tailwind CSS with custom configuration
- **File Upload**: React Dropzone for drag-and-drop receipt uploads
- **API Communication**: Axios for backend requests

### Key Features
- **Receipt Upload**: Drag-and-drop interface for uploading receipt images/PDFs
- **Mock AI Processing**: Simulates intelligent data extraction from receipts
- **Category Management**: Automatic categorization of business expenses
- **Receipt Management**: View, edit, and delete uploaded receipts
- **Analytics**: Basic spending analysis and category breakdowns
- **Responsive Design**: Works on desktop and mobile devices

### API Endpoints
- `POST /api/receipts/upload` - Upload and process receipts
- `GET /api/receipts` - List all receipts with optional filtering
- `GET /api/receipts/{id}` - Get specific receipt details
- `PUT /api/receipts/{id}` - Update receipt information
- `DELETE /api/receipts/{id}` - Delete a receipt
- `GET /api/analytics/summary` - Get spending analytics
- `GET /api/categories` - Get available expense categories

### Data Structure
- **Receipt**: ID, filename, extracted data, category, confidence score
- **Extracted Data**: Vendor name, amount, tax, date, description, receipt number
- **Categories**: 11 predefined business expense categories
- **In-memory storage**: No database setup required for development