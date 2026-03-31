# 🏨 AI Hotel Booking Assistant

A complete AI-powered hotel booking assistant built with Streamlit and LangChain, featuring natural language understanding, structured data extraction, and tool-based reasoning.

## ✨ Features

- **Natural Language Understanding**: Extract user preferences from conversational input
- **Smart Hotel Search**: Filter by location, budget, amenities, and guest count
- **Tool-Based Architecture**: Uses structured tools for reliable operations
- **Beautiful UI**: Modern Streamlit interface with hotel cards and booking flow
- **Booking Management**: Complete booking simulation with confirmations
- **Conversational Memory**: Maintains context throughout the booking journey

## 🏗️ Architecture

```
AI_UseCase/
│
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── models/
│   └── llm.py                     # LLM integration (Groq)
│
├── services/
│   ├── hotel_service.py           # Hotel search and filtering
│   └── booking_service.py         # Booking management
│
├── utils/
│   ├── parser.py                  # Intent/entity extraction
│   ├── prompts.py                 # System prompts
│   └── tools.py                   # Tool definitions for LLM
│
└── data/
    └── hotels.json                # Mock hotel dataset
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Groq API key (for LLM functionality)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AIAssistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file (optional)
GROQ_API_KEY=your_groq_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## 🎯 Usage Examples

### Basic Search
```
User: "Find me a hotel in Bangalore under 5000"
Assistant: Shows 3-5 hotel options within budget
```

### Refinement
```
User: "Only with pool and wifi"
Assistant: Filters previous results to show only hotels with pool and wifi
```

### Booking
```
User: "Book the first one"
Assistant: Confirms booking details and generates booking ID
```

## 🔧 Core Components

### 1. Intent & Entity Extraction
- Uses LLM with structured output parsing
- Extracts: location, budget, guests, dates, preferences
- Fallback to regex-based parsing for robustness

### 2. Hotel Search Engine
- Filters by location, budget, amenities
- Ranks results by relevance score
- Returns top 5 recommendations

### 3. Booking System
- Generates unique booking IDs
- Calculates total costs
- Stores booking history
- Supports cancellations and modifications

### 4. Tool-Based LLM Integration
- Structured tool definitions
- Reliable execution vs. raw LLM responses
- Error handling and fallbacks

## 📊 Hotel Dataset

The system includes 20 mock hotels across 10 cities with:
- Name, location, price per night
- Rating, category (budget/mid-range/luxury)
- Amenities (wifi, pool, breakfast, etc.)
- Descriptions

## 🎨 UI Features

- **Hotel Cards**: Expandable cards with full details
- **Booking Flow**: Clear stages (Search → Refinement → Selection → Booking → Confirmation)
- **Chat Interface**: Conversational AI assistant
- **Quick Suggestions**: Pre-defined query buttons
- **Responsive Design**: Works on desktop and mobile

## 🔍 Advanced Features

### Search Filters
- Location (required)
- Budget (hard filter)
- Number of guests
- Specific amenities
- Number of nights

### Ranking Algorithm
- Rating weight (40%)
- Budget match (30%)
- Amenities match (20%)
- Category preference (10%)

### Booking Management
- Unique booking IDs
- Total cost calculation
- Booking history
- Cancellation with refund policy

## 🛠️ Configuration

### LLM Settings
Edit `models/llm.py` to configure:
- API key
- Model selection
- Temperature settings

### Hotel Data
Add/modify hotels in `data/hotels.json`:
```json
{
  "id": 21,
  "name": "New Hotel",
  "location": "City",
  "price_per_night": 3000,
  "rating": 4.0,
  "amenities": ["wifi", "pool"],
  "category": "mid-range"
}
```

## 🧪 Testing Scenarios

The system handles:
- ✅ Missing information queries
- ✅ Multi-turn conversations
- ✅ Booking flow completion
- ✅ Error handling and fallbacks
- ✅ Refinement and filtering

## 📈 Future Enhancements

- Real hotel API integration
- Payment processing
- Email confirmations
- User accounts and profiles
- Reviews and ratings
- Advanced date parsing
- Map integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is for educational purposes. Please ensure you have proper API keys and permissions for production use.

## 🆘 Support

For issues or questions:
- Check the troubleshooting section
- Review the code comments
- Open an issue on GitHub

---

**Built with ❤️ using Streamlit, LangChain, and Groq**
