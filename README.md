# Medical LLM Comparative Evaluation Platform

A web-based platform for evaluating how well different Large Language Models (LLMs) handle outdated medical information. The system provides real-time comparative assessment of Claude, GPT-5, Gemini, and DeepSeek on medical queries, with automated safety scoring and bias mitigation.

## Project Overview

This platform addresses the critical challenge of outdated medical information in LLM responses by:

- Implementing question-type-aware evaluation (direct, indirect, conversational prompts)
- Using validated LLM-as-Judge methodology with Claude Sonnet 4.5
- Providing real-time comparative scores across multiple models
- Presenting accessible results for non-expert users

## System Architecture

The system follows a client-server architecture:

- React frontend handles user interaction and visualization
- FastAPI backend manages authentication, conversation logic, and evaluation orchestration
- External LLM APIs generate responses
- Claude Sonnet 4.5 serves as the evaluation judge
- SQLite stores user and conversation data

## Project Structure

```
medical-llm-evaluation/
├── backend/                   # FastAPI backend server
│   ├── main.py                # Application entry point
│   ├── auth.py                # Authentication & authorization
│   ├── email_service.py       # Email functionality (password reset)
│   ├── security.py            # Security utilities (JWT, hashing)
│   ├── schemas.py             # Pydantic data models
│   ├── create_users_table.py  # Database initialization script
│   ├── medical_llm_benchmark.db # SQLite database (created on first run)
│   │
│   ├── models/                # Core evaluation logic
│   │   ├── database.py        # Database ORM models
│   │   ├── user.py            # User model
│   │   ├── llm_client.py      # LLM API integrations (4 providers)
│   │   ├── prompt_detector.py # Question classification module
│   │   ├── scoring.py         # LLM-as-Judge scoring engine
│   │   ├── reference_loader.py# Reference data loader
│   │   └── references_routes.py# Reference data API endpoints
│   │
│   ├── references/            # Reference datasets
│   │   ├── medicines_output_medicines_en.xlsx # Withdrawn drugs (EMA)
│   │   ├── icd10pcs_order_2026.txt           # Medical procedures
│   │   └── few_shot_examples.json            # Classification examples
│   │
│   └── utils/                 # Helper utilities
│
├── frontend/                  # React frontend application
│   ├── public/               # Static assets
│   │   └── index.html
│   │
│   └── src/                  # React source code
│       ├── App.js            # Main application component
│       ├── App.test.js       # Frontend tests
│       ├── AuthContext.js    # Authentication state management
│       ├── Navbar.js         # Navigation bar component
│       ├── Login.js          # Login page
│       ├── Register.js       # Registration page
│       ├── ForgotPassword.js # Password reset request
│       ├── ResetPassword.js  # Password reset form
│       ├── PageGuide.js      # Usage guidance component
│       ├── References.js     # Reference data display
│       ├── LoadingEstimate.js# Loading progress indicator
│       ├── ScoringTable.js   # Score visualization table
│       └── ScoreChart.js     # Category performance charts
│
├── tests/                    # Backend tests
│   ├── test_api.py          # API endpoint tests
│   ├── test_prompt_detection.py    # Classification tests
│   ├── test_direct_scoring.py      # Direct prompt scoring tests
│   ├── test_indirect_scoring.py    # Indirect prompt scoring tests
│   └── test_conversational_scoring.py # Conversational scoring tests
│
├── data/                     # Data storage (generated at runtime)
│   ├── responses/           # Cached LLM responses
│   └── scores/              # Evaluation scores
│
├── requirements.txt          # Python dependencies
├── pytest.ini               # Pytest configuration
└── README.md                # This file
```

## Tech Stack

**Backend:**

- Python 3.10+
- FastAPI 0.115.5
- SQLAlchemy 2.0.36 (SQLite database)
- Uvicorn (ASGI server)

**Frontend:**

- React 18+
- Modern JavaScript/JSX

**External APIs:**

- Anthropic Claude API (Sonnet 4.5)
- OpenAI GPT-5 API
- Google Gemini API (Flash 2.5)
- DeepSeek API

**Authentication & Security:**

- JWT tokens (PyJWT, python-jose)
- bcrypt password hashing
- OAuth (Google, GitHub)
- Email-based password reset

## Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 16+ and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/liuqingqing031122/llm_safety_testing.git
cd llm-safety-testing
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the **project root** with the following:

```env
# LLM API Keys (Required for evaluation)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Google OAuth (Optional - for Google login)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# GitHub OAuth (Optional - for GitHub login)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback

# Resend Configuration (Required for password reset emails)
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=your_verified_sender_email

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

**Frontend `.env` file** (in `frontend/` directory):

```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

**Note**:

- Get API keys from: [OpenAI](https://platform.openai.com/api-keys), [Anthropic](https://console.anthropic.com/), [Google AI Studio](https://makersuite.google.com/app/apikey), [DeepSeek](https://platform.deepseek.com/)
- For password reset: Sign up at [Resend](https://resend.com/) and verify your sender email
- OAuth credentials are optional - users can register with email/password

#### Initialize Database

```bash
python backend/create_users_table.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
# From project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Start Frontend Development Server

```bash
# In a new terminal
cd frontend
npm start
```

Frontend will be available at: `http://localhost:3000`

## Running Frontend Tests

```bash
cd frontend
npm test
```

## Running Backend Tests

```bash
# From project root
pytest
```

## Testing Strategy

The backend includes unit tests for:

- Prompt type detection logic
- Direct, indirect, and conversational scoring branches
- API endpoint validation

LLM responses are mocked to ensure deterministic and cost-free testing.

Frontend tests validate:

- Input interaction
- Button state logic
- Response rendering

## Usage Quick Start

1. **Access the platform** at `http://localhost:3000`
2. **(Optional) Create an account** for conversation history
3. **Enter a medical question** (e.g., "Is Esmya safe for treating fibroids?")
4. **Select 2-4 models** to evaluate
5. **View responses** from each model
6. **Click "Start Scoring"** to get automated safety evaluation
7. **Review results**: safest model, best response, and category scores

See [manual.md](manual.md) for detailed user guide.

## Important Notes

### API Costs

- This platform makes multiple API calls per evaluation (5 runs × selected models + scoring)
- **Each evaluation costs money** through LLM provider APIs
- **Deployed version uses researcher's API keys** - not for public deployment

### Academic Use

- This is a research prototype for academic evaluation
- **Not a medical advice tool** - always consult healthcare professionals
- Platform displays medical disclaimers to users

### Limitations

- Evaluation based on withdrawn drugs and outdated guidelines as test cases
- LLM-as-Judge correlation with human judgment: r=0.648-0.755
- API rate limits may affect concurrent evaluation speed

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens for session management
- User data stored locally in SQLite database
- API keys stored in environment variables (never commit `.env` to git)
- Response anonymization during scoring to prevent bias

## 📊 Database Schema

The SQLite database includes four main tables:

- `users`: User accounts and authentication
- `conversations`: Conversation metadata
- `conversation_turns`: Individual turns in conversations
- `model_responses`: LLM responses with scores

Database is automatically created on first run.

## Troubleshooting

### Backend won't start

- Check `.env` file exists in backend folder with required API keys
- Verify Python dependencies: `pip install -r requirements.txt`
- Check port 8000 is not already in use: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)

### Frontend won't connect to backend

- Ensure backend is running on `http://localhost:8000`
- Check `frontend/.env` contains `REACT_APP_API_BASE_URL=http://localhost:8000`
- Verify CORS settings in `backend/main.py` allow `http://localhost:3000`
- Check browser console for error messages

### Scoring fails

- Verify `ANTHROPIC_API_KEY` is valid and has available credits (used for scoring)
- Check API rate limits haven't been exceeded
- Review backend terminal logs for detailed error messages
- Ensure all 4 LLM API keys are configured if evaluating all models

### Email password reset not working

- Verify `RESEND_API_KEY` is set in backend `.env`
- Check `RESEND_FROM_EMAIL` is verified in your Resend dashboard
- Confirm `FRONTEND_URL` points to `http://localhost:3000` (or your deployed URL)
- Check backend logs for email sending errors
- Note: Resend free tier has sending limits - check your account quota

### OAuth login not working

- Verify OAuth credentials (`GOOGLE_CLIENT_ID`, `GITHUB_CLIENT_ID`, etc.) are set
- Check redirect URIs match your configuration (`http://localhost:8000/api/auth/google/callback`)
- Ensure OAuth apps are configured in Google/GitHub developer consoles
- Confirm authorized redirect URIs are whitelisted in provider settings

### "Module not found" errors

- Backend: Ensure you're in project root and ran `pip install -r requirements.txt`
- Frontend: Ensure you're in `frontend/` directory and ran `npm install`
- Check Python version: `python --version` (requires 3.10+)
- Check Node version: `node --version` (requires 16+)

## License

Academic project for educational purposes.

## Contact

For questions about this project or technical issues, please contact:

Qingqing Liu - 2756053L@student.gla.ac.uk

For academic supervision inquiries, please contact through the School of Computing Science.

## Acknowledgments

- Anthropic, OpenAI, Google, DeepSeek for LLM API access
- University of Glasgow School of Computing Science
- Project supervisor for guidance and feedback
- User study participants for valuable evaluation feedback
