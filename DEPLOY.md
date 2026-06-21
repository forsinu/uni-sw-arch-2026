# Deployment Guide

This document describes how to start the backend and frontend services for the project.

---

### Instructions to run Backend
```
#!/bin/bash
# Enter in Backend directory
cd Backend/

# Create a Python Virtual Environment
python -m venv .venv
source .venv/bin/activate

# Install the requirement
pip install python-dotenv

# Start the application
python deploy.py start
```
---

## Instruction to run Frontend

```
#!/bin/bash
# Enter in Frontend directory
cd Frontend/

# Build and start the container
docker compose up --build
```
