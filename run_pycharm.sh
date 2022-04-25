export DB_URI=postgresql://pi_user:password@localhost/pi_coursework
uvicorn src.api.app:app --port 8008 --reload