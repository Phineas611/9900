```bash

## Manually installation steps

IN windows system
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass  
python -m venv venv  
.\venv\Scripts\Activate.ps1 
cd backend
pip3 install -r requirements.txt

## Architecture

Backend folder uses Python
Its using fastapi for REST API route handling
uvicorn to run the web app
pydantic to control models passed betweenlayers
sqlalchemy for the database

## Backend

-Presentation layer to handle API routes
uvicorn app.main:app --reload --port 5000
docs in http://localhost:5000/docs

## Frontend
run npm run dev

## Infrastructure

This runs on localhost port 
# Maintainers
(@unsw.edu.au)

# Render 
https://legalcontractanalyzer-backend.onrender.com/docs