# agentgroup

A multi-agent discussion platform featuring three distinct AI frameworks (Rig, Eliza, and Swarms) engaging in topic-based conversations with a matrix-inspired interface.

## Features

- **Multi-Agent Architecture**: Leverages three different AI frameworks:
  - Rig: Rust-based inference framework
  - Eliza: Pattern-matching conversational agent
  - Swarms: Distributed AI processing framework
- **Matrix-Themed UI**: Terminal-style interface with dynamic matrix rain animation
- **Rate Limiting & Queue Management**: Redis-powered queue system with microsecond-precise response timing
- **User Interaction**: Create topics, ask questions, and vote on agent responses
- **Performance Analytics**: Track and display agent response times

## Architecture

### Frontend (React + TypeScript)
- Matrix-themed UI components
- Real-time response updates
- Responsive design with Tailwind CSS

### Backend (FastAPI + Python)
- RESTful API endpoints
- Redis-based queue management
- Multi-agent coordination
- Response timing analytics

### Database & Caching
- Redis for queue management and caching
- Microsecond-precise timing measurements
- Rate limiting implementation

## Setup & Installation

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.12+
- Redis server
- Poetry (Python package manager)

### Frontend Setup
```bash
# Install dependencies
pnpm install

# Set up environment variables
cp .env.example .env
# Configure VITE_API_URL in .env

# Start development server
pnpm dev
```

### Backend Setup
```bash
# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Configure required API keys and Redis URL

# Start development server
poetry run uvicorn app.main:app --reload
```

## Usage

1. **Create a Topic**: Start a new discussion topic through the web interface
2. **Ask Questions**: Submit questions on any topic
3. **View Responses**: Each AI agent will provide its perspective
4. **Vote on Responses**: Users can vote for the most helpful responses
5. **Track Performance**: Monitor agent response times and queue status

## Development

### Branch Naming Convention
- Format: `devin/{timestamp}-{descriptive-slug}`
- Example: `devin/1737949573-rename-project`

### Pull Request Guidelines
1. Ensure all tests pass
2. Update documentation as needed
3. Follow the existing code style
4. Include clear PR descriptions

## Contributing

1. Fork the repository
2. Create your feature branch following the naming convention
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details

## Project Status

Active development - See Issues for current tasks and feature requests.
