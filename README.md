# Intelligent Resume Screener

## Overview
The **Intelligent Resume Screener** is an AI-powered application designed to automatically analyze and evaluate resumes, helping recruiters quickly identify top candidates. By leveraging the Gemini API, it provides intelligent insights into candidate qualifications and streamlines the hiring process.

---

## Features
- Automatic parsing and scoring of resumes.
- AI-driven insights to match candidates with job requirements.
- Simple and extensible backend built with FastAPI.
- Easy switching from development SQLite database to production PostgreSQL.

---

## Tech Stack
- **Backend:** FastAPI  
- **Database:** SQLite (development), PostgreSQL (planned for production)  
- **AI Integration:** Gemini API  

---

## Project Structure
project-root/
├── backend/
│ └── app/
├── .env.example
├── README.md


---

## Setup & Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd Resume_Screener/backend
Create and activate a virtual environment:

Windows

python -m venv venv
.\venv\Scripts\activate
Mac/Linux

python -m venv venv
source venv/bin/activate
Install dependencies:

pip install -r requirements.txt
Set up environment variables:

cp .env.example backend/.env
Running the Application
Start the FastAPI server:

uvicorn app.main:app --reload
Visit http://127.0.0.1:8000/docs to access the interactive API documentation.

Future Improvements
Integration with PostgreSQL for production use.

Frontend dashboard for recruiters.

Enhanced AI scoring models and analytics.

