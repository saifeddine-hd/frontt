# SecretHawk 🦅

A powerful, production-ready secret scanner that detects exposed API keys, tokens, and sensitive data in your codebase.

## Features

- 🔍 **Multi-engine scanning**: Combines regex patterns with Gitleaks for comprehensive detection
- 🔄 **Repository monitoring**: Automatic GitHub/GitLab repository monitoring with webhooks
- 🚨 **Discord notifications**: Real-time alerts with remediation guides
- 🛡️ **Security-first**: Automatic secret masking and secure handling
- 🚀 **Modern UI**: React frontend with real-time scanning results
- 🔌 **REST API**: FastAPI backend with JWT authentication
- 📊 **Rich exports**: JSON, CSV, and PDF reporting
- 🐳 **Docker ready**: Full containerization for easy deployment
- ⚡ **Fast CI/CD**: GitHub Actions integration

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <your-repo>
cd SecretHawk
cp .env.example .env

# Start with Docker Compose
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### CLI Usage

```bash
# Install CLI
pip install -r cli/requirements.txt

# Scan a directory
python cli/secrethawk.py scan ./my-project

# Scan with custom patterns
python cli/secrethawk.py scan ./my-project --patterns custom-patterns.yaml

# Export results
python cli/secrethawk.py scan ./my-project --output results.json
```

### Repository Monitoring

```bash
# Add repository via API
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-repo",
    "url": "https://github.com/user/repo",
    "provider": "github",
    "token": "ghp_xxxxxxxxxxxx",
    "discord_webhook_url": "https://discord.com/api/webhooks/..."
  }'
```

## Supported Secret Types

- AWS Access Keys & Secret Keys
- Google Cloud Service Account Keys
- GitHub Personal Access Tokens
- Stripe API Keys
- Slack Bot Tokens
- JWT Tokens
- Private Keys (RSA, DSA, EC)
- Database Connection Strings
- Custom patterns via YAML configuration

## Architecture

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + SQLite
- **Scanner**: Python + Gitleaks integration
- **Security**: JWT authentication, automatic secret redaction
- **Deployment**: Vercel (frontend) + Render (backend)

## Deployment

### Frontend (Vercel)
```bash
cd apps/web
npm run build
# Deploy to Vercel
```

### Backend (Render/Railway)
```bash
cd apps/api
# Deploy using Dockerfile
```

## Security & Privacy

SecretHawk is designed with privacy by default:
- Secrets are automatically masked in all outputs
- Temporary files are cleaned after scanning
- No data retention beyond active sessions
- GDPR-friendly minimal logging

See [PRIVACY.md](PRIVACY.md) for full details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest apps/api/tests/`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and improvements.