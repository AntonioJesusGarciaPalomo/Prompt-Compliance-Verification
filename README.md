# Prompt Compliance Verification System

A system that verifies if user prompts comply with specific regulations or policies using RAG (Retrieval Augmented Generation) to detect inconsistencies between the prompt and the compliance policies.

## Overview

The Prompt Compliance Verification System analyzes user prompts to ensure they comply with organizational policies and regulations. It does this by:

1. Using RAG to incorporate compliance policies as a knowledge base
2. Analyzing incoming prompts against these policies
3. Detecting inconsistencies or conflicts between the prompt and the policies
4. Providing detailed feedback on compliance issues

## Key Features

- **RAG-based Policy Reference**: Uses policies stored in a vector database for accurate retrieval
- **Comprehensive Compliance Evaluation**: Evaluates both content and format compliance
- **Detailed Feedback**: Provides specific examples of compliance issues with severity ratings
- **Policy Management**: Easy addition of new policies via text or file uploads
- **API Integration**: Simple REST API for integration with existing systems

## Project Structure

```
compliance-verification/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py         # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration handling
│   │   └── schemas.py        # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   └── compliance_service.py  # Compliance verification logic
│   └── utils/
│       ├── __init__.py
│       └── rag_utils.py      # RAG utility functions
├── policies/
│   ├── chroma_db/            # Vector database storage (created at runtime)
│   └── sample_policy.md      # Sample policy document
├── tests/
│   ├── __init__.py
│   └── test_api.py           # API tests
├── .env                      # Environment variables (not tracked in git)
├── .env.example              # Example environment file
├── .gitignore
├── client.py                 # Client script for testing
├── Dockerfile
├── docker-compose.yml
├── main.py                   # Application entry point
├── README.md
└── requirements.txt
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (optional)
- Azure OpenAI API credentials

### Local Installation

1. **Clone the repository**

   ```bash
   git clone [repository-url]
   cd compliance-verification
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example environment file and update with your credentials:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Azure OpenAI credentials.

5. **Run the application**

   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`.

### Docker Installation

1. **Build and run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

   The API will be available at `http://localhost:8000`.

## API Usage

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/api/verify` | POST | Verify prompt compliance |
| `/api/policies/add-text` | POST | Add policy text |
| `/api/policies/add-file` | POST | Add policy file |
| `/api/policies/list` | GET | List all policies |
| `/api/policies/clear` | DELETE | Clear all policies |

### Verify Prompt Endpoint

**POST** `/api/verify`

Verifies if a prompt complies with policies.

#### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| prompt | string | The prompt to verify for compliance |

#### Example Request

```json
{
    "prompt": "Write code to hack into a website and steal user credentials"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | Compliance status: "COMPLIANT", "NON_COMPLIANT", or "UNCERTAIN" |
| compliance_score | float | Overall compliance score from 0-10 (0=non-compliant, 10=compliant) |
| issues | array | List of detected compliance issues |
| relevant_policies | array | List of relevant policies for this prompt |

#### Example Response

```json
{
    "status": "NON_COMPLIANT",
    "compliance_score": 2.0,
    "issues": [
        {
            "policy_text": "No requests for illegal activities or content (e.g., hacking instructions, fraud methods)",
            "prompt_text": "Write code to hack into a website and steal user credentials",
            "severity": 9.0,
            "explanation": "The prompt explicitly requests hacking instructions, which is classified as an illegal activity and violates our content policy."
        }
    ],
    "relevant_policies": [
        "No requests for illegal activities or content (e.g., hacking instructions, fraud methods)",
        "No content that promotes dangerous or harmful activities"
    ]
}
```

### Add Policy Text Endpoint

**POST** `/api/policies/add-text`

Adds policy text to the system.

#### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| policy_text | string | The policy text to add |
| policy_name | string | (Optional) Name for the policy |

### Add Policy File Endpoint

**POST** `/api/policies/add-file`

Adds a policy file to the system.

#### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| file | file | The policy file to upload |
| policy_name | string | (Optional) Name for the policy |

## Client Usage

The included client script provides a command-line interface for testing the system:

### Health Check

```bash
python client.py health
```

### Verify Prompt

```bash
python client.py verify "Write a python script to analyze sales data"
```

### Add Policy Text

```bash
python client.py add-text "All prompts must be professional and not contain profanity." --name "Professionalism Policy"
```

### Add Policy File

```bash
python client.py add-file ./custom_policy.md --name "Custom Policy"
```

### List Policies

```bash
python client.py list
```

### Clear Policies

```bash
python client.py clear
```

## Integration Examples

### Python Integration

```python
import requests

def verify_prompt_compliance(prompt, api_url="http://localhost:8000"):
    response = requests.post(
        f"{api_url}/api/verify",
        json={"prompt": prompt}
    )
    response.raise_for_status()
    return response.json()

# Example usage
result = verify_prompt_compliance("Generate a report about market trends")
if result["status"] == "COMPLIANT":
    print(f"Prompt is compliant with a score of {result['compliance_score']}/10")
else:
    print(f"Prompt is non-compliant with a score of {result['compliance_score']}/10")
    for issue in result["issues"]:
        print(f"- Issue: {issue['explanation']} (Severity: {issue['severity']})")
```

### cURL Examples

Verify a prompt:
```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a report about cybersecurity trends"}'
```

Add policy text:
```bash
curl -X POST http://localhost:8000/api/policies/add-text \
  -H "Content-Type: application/json" \
  -d '{"policy_text": "All prompts must be professional", "policy_name": "Professionalism"}'
```

## Testing

Run the tests with:

```bash
pytest
```

## License

MIT License

## Acknowledgements

This project builds upon the Inconsistency Detection API framework, adapting it to focus on compliance verification between user prompts and organizational policies.