## Prerequisites
- Python >= 3.8 installed on your system
- pip (Python package manager) installed

## Steps

### 1. Create a Virtual Environment
To isolate the project dependencies, create a virtual environment named `venv`.

```bash
python -m venv venv
```

Activate the virtual environment:
- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 2. Install Requirements
Install the required dependencies from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 3. Add a `.env` File
Create a `.env` file in the project's root directory to store environment-specific settings, such as secret keys and database credentials. Use the following format:

```
I will share it
```

Ensure the `.env` file is included in `.gitignore` to prevent it from being tracked by version control.

### 4. Apply Migrations
Run the following commands to apply database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start the Server
Start the development server to run the project locally:

```bash
python manage.py runserver
```

The server will be available at `http://127.0.0.1:8000/` by default.

## Additional Notes
- If you encounter any issues, ensure all required dependencies are installed.
- To deactivate the virtual environment, use:
  ```bash
  deactivate
  ```

