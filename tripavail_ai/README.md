# TripAvail AI 🗓️

An AI-powered travel content automation system that generates and posts engaging travel videos to Instagram, Facebook, and YouTube.

## 🆕 Phase 2 Development Sandbox Available!

**Want to experiment with new features safely?** Check out the Phase 2 sandbox:
- 📁 **Isolated environment** - Won't affect production
- 🧪 **Full test suite** - 5/5 tests passing
- 🛡️ **Protected credentials** - Separate `.env_sandbox`
- 🚀 **Quick start**: `.\START_PHASE2.ps1`

See [`PHASE2_QUICKSTART.md`](PHASE2_QUICKSTART.md) for details.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- FFmpeg (for video processing)
- DigitalOcean droplet (4 GB RAM, 80 GB SSD recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd tripavail_ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env_template.txt .env
   # Edit .env and add your API keys
   ```

5. **Install system dependencies (Ubuntu/Debian)**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git ffmpeg curl
   ```

## 🔑 Required API Keys

Add the following keys to your `.env` file:

- `OPENAI_API_KEY` - OpenAI API key for AI functionality
- `NEWSCATCHER_API_KEY` - NewsCatcher API key for news aggregation
- `META_PAGE_TOKEN` - Meta Page Token for Facebook integration
- `YOUTUBE_API_KEY` - YouTube API key for video content

## 📁 Project Structure

```
tripavail_ai/
├── modules/          # Core application modules
├── data/            # Data storage and processing
├── config/          # Configuration files
├── logs/            # Application logs
├── requirements.txt # Python dependencies
├── .gitignore      # Git ignore rules
└── env_template.txt # Environment variables template
```

## 🛠️ Development Setup

### DigitalOcean Droplet Setup

1. Create a new droplet (Ubuntu 22.04 LTS)
2. Configure SSH access
3. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git ffmpeg curl
   ```

### Local Development

1. Activate virtual environment
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

- Copy `env_template.txt` to `.env`
- Fill in your API keys
- Configure additional settings as needed

## 📝 Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=modules
```

## 📊 Monitoring & Logging

The system uses a centralized logging setup for consistent, structured logs across all modules.

### Log Files

All logs are stored in the `logs/` directory with automatic rotation and retention:

- **`app.log`** - All application logs (INFO and above)
- **`app_error.log`** - Error-only logs for quick troubleshooting
- **`app.jsonl`** - Optional JSON-formatted logs for machine parsing (enable via `LOG_JSON=true`)

Legacy per-module logs (e.g., `fourhour.log`, `tourism_editor.log`) continue working during migration.

### Configuration

Control logging behavior via environment variables or `config/settings.py`:

```bash
# .env configuration
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs            # Custom log directory
LOG_JSON=false          # Enable JSON logs for analytics
```

Settings in `config/settings.py`:
- `LOG_LEVEL` - Default: `INFO`
- `LOG_ROTATION` - Default: `1 day` (also supports size: `10 MB`)
- `LOG_RETENTION` - Default: `30 days` (older logs auto-deleted)

### Rotation & Retention

- **Automatic rotation**: Logs rotate daily (or by size) and are compressed to `.zip`
- **Automatic cleanup**: Logs older than 30 days are deleted to save disk space
- **Safe defaults**: Prevents uncontrolled log growth in production

### Using Logs

```python
# In any module, just import and use:
from loguru import logger

logger.info("Processing post...")
logger.error("API call failed", error=str(e))
logger.debug("Detailed trace info", query=query)
```

Standard library `logging` also works seamlessly:
```python
import logging
logging.getLogger(__name__).info("This flows through Loguru!")
```

### Monitoring in Production

```bash
# Tail live logs
tail -f logs/app.log

# Check recent errors
tail -n 100 logs/app_error.log

# Search for specific events
grep "Shutterstock" logs/app.log

# Monitor log disk usage
du -sh logs/
```

## 🔒 Security

- Never commit `.env` files
- Use environment variables for sensitive data
- Regularly rotate API keys
- Monitor API usage and costs

## 📚 API Documentation

- OpenAI API: https://platform.openai.com/docs
- NewsCatcher API: https://newscatcher.com/docs
- Meta Graph API: https://developers.facebook.com/docs/graph-api
- YouTube Data API: https://developers.google.com/youtube/v3

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review API documentation
- Check rate limits and quotas
