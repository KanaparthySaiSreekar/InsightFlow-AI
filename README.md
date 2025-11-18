# InsightFlow AI

**AI-Powered Business Intelligence Tool**

InsightFlow AI is a web-based platform that democratizes data analysis by allowing users to upload raw data files (CSV, Excel, JSON) or connect to databases. The system automatically normalizes this data into a high-performance DuckDB instance and uses Large Language Models (LLMs) to generate schemas. Users can then query their data using natural language via a chat interface to receive answers in the form of text, dynamic tables, and interactive charts.

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Multi-Format Support**: Upload CSV, Excel, JSON, or SQLite files
- **AI-Powered Schema Generation**: Automatically understand your data structure
- **Text-to-SQL Conversion**: LLM converts your questions to SQL queries
- **Interactive Visualizations**: Auto-generated charts (bar, line, pie, scatter)
- **Multi-LLM Support**: Choose between OpenAI, Google Gemini, or Anthropic Claude
- **BYOK (Bring Your Own Key)**: Secure, encrypted storage of your API keys
- **Self-Healing Queries**: Automatically fixes SQL errors
- **Chat History**: Persistent conversation history for each project

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Application database for users and chat history
- **DuckDB**: In-process OLAP database for analytical queries
- **LangChain**: LLM orchestration framework
- **SQLAlchemy**: ORM for database management

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Data visualization library
- **Axios**: HTTP client

## Architecture

```
┌─────────────┐
│   Frontend  │  Next.js + React
│  (Port 3000)│
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   Backend   │  FastAPI
│  (Port 8000)│
└──────┬──────┘
       │
       ├─► PostgreSQL (User data, chats)
       ├─► DuckDB (User uploaded data)
       └─► LLM APIs (OpenAI/Google/Anthropic)
```

## Prerequisites

- **Docker & Docker Compose** (recommended)
  OR
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+**

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/InsightFlow-AI.git
cd InsightFlow-AI
```

### 2. Generate Encryption Key

Generate a Fernet encryption key for API key storage:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Configure Environment

Edit `docker-compose.yml` and replace:
- `your-secret-key-change-in-production` with a strong secret key
- `your-fernet-key-change-in-production` with the key generated in step 2

### 4. Start the Application

```bash
docker-compose up -d
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Manual Setup (Without Docker)

### Backend Setup

1. **Navigate to backend directory**

```bash
cd backend
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL`: Your PostgreSQL connection string
- `SECRET_KEY`: A random secret key for JWT
- `ENCRYPTION_KEY`: Generate using the command from Quick Start step 2

5. **Run the backend**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**

```bash
cd frontend
```

2. **Install dependencies**

```bash
npm install
```

3. **Configure environment**

```bash
cp .env.example .env
```

Edit `.env` and set:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000/api/v1)

4. **Run the frontend**

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Usage Guide

### 1. Sign Up / Login

- Navigate to http://localhost:3000
- Create a new account or log in

### 2. Configure LLM API Key

- On the dashboard, click "Configure LLM"
- Select your preferred provider (OpenAI, Google, or Anthropic)
- Enter your API key
- Click "Save"

**Getting API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Google: https://makersuite.google.com/app/apikey
- Anthropic: https://console.anthropic.com/

### 3. Upload Data

- Click "Upload Data File"
- Enter a project name and description
- Upload your CSV, Excel, or JSON file
- Wait for the system to process and analyze your data

### 4. Chat with Your Data

- Click on a project to open the chat interface
- Ask questions in natural language:
  - "What are the top 10 sales by region?"
  - "Show me the trend of revenue over time"
  - "Which product has the highest profit margin?"
- View results as tables or charts
- Export data as needed

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login/json` - Login
- `GET /api/v1/auth/me` - Get current user

### LLM Configuration
- `POST /api/v1/llm-config/` - Create/update LLM config
- `GET /api/v1/llm-config/active` - Get active config

### Projects
- `POST /api/v1/projects/` - Upload data file
- `GET /api/v1/projects/` - List projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}/schema` - Update schema

### Chat
- `POST /api/v1/chat/` - Create new chat
- `GET /api/v1/chat/` - List chats
- `POST /api/v1/chat/query` - Send query

Full API documentation: http://localhost:8000/docs

## Development

### Project Structure

```
InsightFlow-AI/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Security, dependencies
│   │   ├── db/            # Database config
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── config.py      # Settings
│   │   └── main.py        # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts
│   │   ├── lib/           # API client
│   │   └── types/         # TypeScript types
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

### Running Tests

Backend tests:
```bash
cd backend
pytest
```

Frontend tests:
```bash
cd frontend
npm test
```

## Security Considerations

- All API keys are encrypted using Fernet encryption
- JWT tokens for authentication
- CORS protection
- SQL injection prevention through parameterized queries
- User data isolation (one user cannot access another's DuckDB files)

## Performance

- DuckDB provides fast analytical queries (< 5 seconds for datasets under 1GB)
- Optimized for concurrent users with async FastAPI
- Automatic query optimization by LLM

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Ensure all dependencies are installed

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in frontend `.env`
- Check CORS settings in backend `config.py`

### LLM queries failing
- Verify your API key is correct
- Check API key has sufficient credits/quota
- Review error messages in chat interface

### File upload fails
- Check file format is supported (.csv, .xlsx, .json)
- Verify file size is under 1GB
- Check backend logs for detailed error

## Roadmap

### Phase 2: Visualization & Multi-LLM (Current)
- ✅ Multiple LLM provider support
- ✅ Interactive charts and visualizations
- ✅ Chat history persistence

### Phase 3: Advanced Features (Planned)
- [ ] Live database connections (Postgres/MySQL)
- [ ] "Explain this chart" feature
- [ ] Shareable dashboards
- [ ] Collaborative workspaces
- [ ] Export to PDF/Excel
- [ ] Scheduled reports

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/InsightFlow-AI/issues
- Documentation: See `/docs` folder

## Acknowledgments

- Built with FastAPI, Next.js, DuckDB, and LangChain
- Powered by OpenAI, Google Gemini, and Anthropic Claude
- Inspired by the need for accessible data analytics

---

**Made with ❤️ for data enthusiasts**
