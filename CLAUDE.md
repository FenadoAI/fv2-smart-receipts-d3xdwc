# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload
```

### Frontend (React)
```bash
cd frontend
bun install
bun start
```

### Testing
```bash
python backend/test_api.py
```

### Code Quality
```bash
# Backend linting and formatting
cd backend
black .
isort .
flake8 .
mypy .

# Frontend testing
cd frontend
bun test
```

## Architecture Overview

### Backend Structure
- **FastAPI** application with AsyncIOMotorClient for MongoDB
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Pattern**: All routes under `/api` prefix using APIRouter
- **Environment**: Requires `.env` with `MONGO_URL`, `DB_NAME`, `JWT_SECRET_KEY`
- **CORS**: Configured for all origins in development

### Frontend Structure
- **React 19** with React Router v7
- **UI Framework**: shadcn/ui components built on Radix UI
- **Styling**: Tailwind CSS with custom configuration via craco
- **API Communication**: Axios with `REACT_APP_API_URL` (defaults to http://localhost:8000)
- **Components**: Located in `/src/components/ui/` with consistent import pattern `@/components/ui/`

### Database
- **MongoDB** with collections: users, items, status_checks
- **Connection**: AsyncIOMotorClient with environment-based configuration

### Development Patterns
- Backend models use Pydantic with automatic UUID generation and datetime fields
- Frontend components follow React functional pattern with hooks
- API responses follow consistent JSON structure
- Authentication handled via JWT tokens in request headers