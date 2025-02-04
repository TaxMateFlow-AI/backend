# Automated Tax Filing Chatbot Backend

Welcome to the backend repository for the **Automated Tax Filing Chatbot**! This backend is built using **Python FastAPI**, a modern, fast web framework that is ideal for APIs. The backend handles OCR processing for W-2 forms, integrates with the IRS API for tax filing, and powers the chatbot's functionality.

---

## Features of the Backend

- **OCR Integration**: Processes uploaded W-2 forms to extract data using Optical Character Recognition (OCR).
- **IRS API Integration**: Connects with the IRS API to streamline tax filing and retrieval of tax-related information.
- **Chatbot Logic**: Implements the core chatbot functionality for user interaction and tax-related assistance.
- **Secure Data Handling**: Ensures sensitive user data is encrypted and complies with data security standards.
- **Scalable Architecture**: Built with FastAPI to support high-performance and scalability.
- **RESTful APIs**: Provides endpoints to serve the frontend and manage chatbot interactions.

---

## Tech Stack

- **FastAPI**: The web framework for building APIs.
- **Python 3.9+**: The programming language for the backend.
- **Tesseract OCR**: For extracting text from W-2 forms.
- **IRS API**: For tax-related data and filing integration.
- **SQLAlchemy**: For database interactions (or any other ORM of your choice).
- **Uvicorn**: For running the FastAPI app.
- **Pydantic**: For data validation and serialization.
- **JWT**: For user authentication and authorization (optional).

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**
- **pip** (Python package manager)
- **Tesseract OCR** (for OCR functionality, installation instructions below)
- **PostgreSQL/MySQL/SQLite** (any database of your choice)

---

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SenhaoAI/backend.git
   ```

2. Navigate to the project directory:
   ```bash
   cd backend
   ```

3. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Linux/MacOS
   venv\Scripts\activate     # For Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Install Tesseract OCR (required for OCR functionality):
   - **Linux**: 
     ```bash
     sudo apt-get install tesseract-ocr
     ```
   - **MacOS**:
     ```bash
     brew install tesseract
     ```
   - **Windows**:
     Download the installer from [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract) and follow the installation instructions.

---

### Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. The server will start at:
   ```
   http://127.0.0.1:8000
   ```

3. Access the interactive API documentation at:
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Project Structure

The project follows a modular structure:

```
tax-filing-chatbot-backend/
│
├── app/
│   ├── api/                # API route handlers
│   │   ├── v1/             # API versioning (v1 endpoints)
│   │       ├── endpoints/  # Individual endpoint files
│   │       └── __init__.py 
│   ├── core/               # Core configurations (e.g., settings, initialization)
│   ├── models/             # Database models
│   ├── services/           # Business logic (e.g., OCR, IRS API integration, chatbot logic)
│   ├── utils/              # Utility functions (e.g., file processing, validators)
│   ├── main.py             # Entry point for the FastAPI app
│   └── __init__.py
│
├── tests/                  # Unit and integration tests
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── .env                    # Environment variables
```

---

## API Endpoints

Below is a summary of the key endpoints (more details can be found in the Swagger documentation):

### W-2 Form Processing
- **POST `/api/v1/upload-w2`**
  - Uploads a W-2 form (PDF or image) for OCR processing.
  - **Request**: `multipart/form-data` (file)
  - **Response**: Extracted data from the W-2 form.

### Chatbot Interaction
- **POST `/api/v1/chatbot`**
  - Sends user queries to the chatbot and receives responses.
  - **Request**: JSON payload with the user query.
  - **Response**: Chatbot's response.

### IRS API Integration
- **GET `/api/v1/tax-status`**
  - Fetches tax filing status from the IRS API.
  - **Response**: Tax filing status details.

---

## Environment Variables

Create a `.env` file in the root directory to store sensitive information. Example:

```
DATABASE_URL=postgresql://user:password@localhost/taxbot_db
IRS_API_KEY=your_irs_api_key
SECRET_KEY=your_jwt_secret_key
```

---

## How It Works

1. **W-2 OCR Processing**: Users upload their W-2 forms, which are processed using Tesseract OCR to extract relevant data.
2. **Chatbot Interaction**: Users query the chatbot, which uses natural language processing (NLP) and predefined logic to provide responses.
3. **IRS API Communication**: The backend communicates with the IRS API to retrieve or submit tax-related data.
4. **Data Security**: All sensitive data is encrypted and securely transmitted between the backend and the IRS API.

---

## Testing

Run tests to ensure everything is functioning as expected:

```bash
pytest
```

---

## Future Enhancements

- Implement AI/ML for better chatbot NLP capabilities.
- Add support for additional tax forms such as 1099s.
- Implement rate limiting and caching for API performance optimization.
- Expand logging and monitoring for better error tracking and debugging.

---

## Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your feature description"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.

---

## Acknowledgments

- FastAPI team for providing a robust framework.
- Tesseract OCR for their open-source OCR capabilities.
- The IRS API for making tax data integration possible.

---

Feel free to reach out for any questions or suggestions! 🚀
