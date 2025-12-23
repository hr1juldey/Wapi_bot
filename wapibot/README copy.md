# WAPI Bot - WhatsApp Service Booking Chatbot

Production-ready WhatsApp chatbot for automotive service booking with Frappe ERP integration.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis
- Ollama (for LLM)

### Installation

1. **Clone and setup**
```bash
cd wapibot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Redis**
```bash
docker run -d -p 6379:6379 redis
```

3. **Start Ollama**
```bash
ollama serve
ollama pull gemma3:4b
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run the bot**
```bash
python main.py
```

The server will start on `http://0.0.0.0:8002`

## 📁 Project Structure

```
wapibot/
├── core/                    # Core business logic
│   ├── state/              # State machine
│   ├── data/               # Data management
│   ├── llm/                # LLM integration
│   ├── nlp/                # NLP components
│   └── locks/              # Concurrency control
├── integrations/           # External APIs
│   ├── frappe/            # Frappe ERP
│   └── wapi/              # WhatsApp API
├── orchestrators/          # Main handlers
├── models/                 # Pydantic models
├── config/                 # Configuration
└── main.py                # Entry point
```

## 🔧 Configuration

Edit `.env` file:

```env
# Frappe ERP
FRAPPE_BASE_URL=https://your-frappe-instance.com
FRAPPE_API_KEY=your_api_key
FRAPPE_API_SECRET=your_api_secret

# WAPI
WAPI_BASE_URL=https://api.wapibot.com
WAPI_VENDOR_UID=your_vendor_uid
WAPI_BEARER_TOKEN=your_bearer_token
WAPI_FROM_PHONE_NUMBER_ID=your_phone_id

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 📊 Features

- ✅ Conversational booking flow
- ✅ LLM-powered data extraction
- ✅ State management with Redis
- ✅ Race condition prevention
- ✅ Frappe ERP integration
- ✅ WhatsApp messaging via WAPI

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v
```

## 📖 Documentation

See `docs/` folder for detailed documentation:
- `Documentation_Summary.md` - Overview
- `Implementation_Checklist.md` - Development plan
- `Quick_Reference.md` - Developer guide
- `WAPI_Bot_Flow_Design.md` - Flow diagrams

## 🔄 Conversation Flow

1. **Greeting** → User says "Hi"
2. **Name Collection** → Bot asks for name
3. **Phone Collection** → Bot asks for phone
4. **Vehicle Details** → Bot asks for car details
5. **Date Selection** → Bot asks for date
6. **Confirmation** → Bot shows summary
7. **Completed** → Booking created

## 🛠️ API Endpoints

### Webhook
```
POST /webhook
```

Receives WhatsApp messages from WAPI.

### Health Check
```
GET /
```

Returns service status.

## 📝 License

Proprietary - All rights reserved

## 🤝 Support

For issues or questions, contact the development team.
