import os

# Load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip .env loading

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Network Scanner API Starting...")
    print("  Server: http://localhost:5000")
    print("  Health: http://localhost:5000/api/health")
    print("  Debug:  http://localhost:5000/api/debug/auth-test")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
