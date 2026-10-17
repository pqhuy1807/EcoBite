# EcoBite Backend Setup

This guide explains how to prepare the local Python environment for the EcoBite backend.

## Prerequisites

- Python 3.11 or another version supported by the project dependencies
- Git
- A terminal (Command Prompt, PowerShell, or Bash)

## 1. Navigate to the backend directory

```bash
cd backend
```

Run this command from the root directory of the EcoBite repository.

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows Command Prompt:

```bat
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment variables

Check the project documentation and `../.env.example` for the required environment variables.

Create a local `.env` file only if required by the application. Do not commit passwords, API keys, tokens, or other secrets.

## 5. Run tests

Check the project instructions for the supported test command. If the project uses pytest, run:

```bash
python -m pytest
```

## Notes

- Keep the virtual environment inside `.venv`.
- Do not commit the virtual environment or local secrets.
- Follow the root `README.md` and existing backend documentation for database migrations and application startup commands.