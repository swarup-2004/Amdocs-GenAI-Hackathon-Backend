# Amdocs-GenAI-Hackathon-Backend

## Prerequisites
Ensure you have the following installed on your system:
- Python >= 3.8
- `pip` (Python package manager)

## Setup Guide

### 1. Create a Virtual Environment
To isolate the project dependencies, create a virtual environment named `venv`:

```bash
cd Amdocs-GenAI-Hackathon-Backend
python -m venv venv
```

Activate the virtual environment:
- **On Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **On macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 2. Install Requirements
Install the required dependencies from the `requirements.txt` file:

```bash
pip install -r backend/requirements.txt
```

### 3. Add a `.env` File
Create a `.env` file in the project's root directory to store environment-specific settings, such as secret keys and database credentials. Use the following format:

```
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=

GROQ_API_KEY=
GITHUB_API_KEY=
LINKEDIN_API_KEY=

QDRANT_API_KEY=
QDRANT_URL=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
AURA_INSTANCEID=
AURA_INSTANCENAME=
```

Ensure the `.env` file is included in `.gitignore` to prevent it from being tracked by version control.

### 4. Apply Migrations
Run the following commands to apply database migrations:

```bash
python backend/manage.py makemigrations
python backend/manage.py migrate
```

Create a superuser for Django admin:

```bash
python backend/manage.py createsuperuser
```

### 5. Start the Server
Start the development server to run the project locally:

```bash
python backend/manage.py runserver
```

The server will be available at `http://127.0.0.1:8000/` by default.

## Setup for Qdrant Vector Database
Create three collections in Qdrant with the following schema:

### **1. Learning Modules Collection**
```json
{
  "collection_name": "learning_modules",
  "vectors_config": {
    "size": 384,
    "distance": "COSINE"
  },
  "payload_schema": {
    "roadmap": {
      "topics": ["Array of strings"],
      "prerequisites": ["Array of strings"],
      "weekly_breakdown": ["Array of strings"],
      "key_milestones": ["Array of strings"]
    },
    "practice": {
      "active_recall": "String",
      "hands_on_projects": "String",
      "debugging_scenarios": "String",
      "collaborative_learning": "String"
    }
  }
}
```

### **2. Tests Collection**
```json
{
  "collection_name": "tests_collection",
  "vectors_config": {
    "size": 384,
    "distance": "COSINE"
  },
  "payload_schema": {
    "questions": [
      {
        "question_type": "String",
        "skill_tested": "String",
        "difficulty_tier": "String",
        "question": "String",
        "options": ["Array of strings"],
        "correct_answer": "String",
        "diagnostic_insight": "String"
      }
    ]
  }
}
```

### **3. Courses Collection**
```json
{
  "collection_name": "courses",
  "vectors_config": {
    "size": 384,
    "distance": "COSINE"
  },
  "payload_schema": {
    "title": "String",
    "description": "String",
    "category": "String",
    "difficulty": "String",
    "duration": "String",
    "instructor": "String",
    "rating": "Float",
    "tags": ["Array of strings"],
    "source": "String",
    "url": "String"
  }
}
```
## Additional Notes
- If you encounter any issues, ensure all required dependencies are installed.
- To deactivate the virtual environment, use:
  ```bash
  deactivate
  ```

