# Deployment Documentation

**Quick Summary**: Deployment guides, access information, and production setup for the Epstein Document Archive. .

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [Ngrok Access Guide](./NGROK_ACCESS.md) - Public access via ngrok tunneling
- [Access Information](./ACCESS_INFO.md) - Server access and endpoint information
- **NGROK_ACCESS.md**: Guide for setting up and using ngrok for public access
- Ngrok tunnel configuration
- Public URL generation

---

Deployment guides, access information, and production setup for the Epstein Document Archive.

## Quick Links

- [Ngrok Access Guide](./NGROK_ACCESS.md) - Public access via ngrok tunneling
- [Access Information](./ACCESS_INFO.md) - Server access and endpoint information

## Overview

This directory contains documentation for deploying, accessing, and managing the production environment of the Epstein Document Archive.

## Key Documents

### Public Access
- **NGROK_ACCESS.md**: Guide for setting up and using ngrok for public access
  - Ngrok tunnel configuration
  - Public URL generation
  - Access management
  - Security considerations

### Server Information
- **ACCESS_INFO.md**: Server access details and endpoint information
  - API endpoints
  - Authentication details
  - Port configurations
  - Connection information

## Deployment Options

### Local Development
```bash
# Backend API
cd server
uvicorn api:app --reload --port 8000

# Frontend
cd server/web
npm run dev
```

### Production Deployment

#### Option 1: Ngrok Tunneling
See [NGROK_ACCESS.md](./NGROK_ACCESS.md) for detailed setup.

```bash
# Start backend
cd server
uvicorn api:app --port 8000

# Start ngrok tunnel
ngrok http 8000
```

#### Option 2: Traditional Server
```bash
# Using gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server.api:app

# Using systemd service
sudo systemctl start epstein-api
```

## Access Points

### API Endpoints
- **Local**: http://localhost:8000
- **Ngrok**: https://[random-id].ngrok.io (when tunnel active)
- **Documentation**: http://localhost:8000/docs

### Web Interface
- **Local**: http://localhost:5173 (Vite dev server)
- **Production**: Served via API static files

## Environment Configuration

### Required Environment Variables
```bash
# API Keys
export OPENAI_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"  # If using OpenRouter

# Database
export DATABASE_PATH="/path/to/kuzu_db"

# Server
export API_PORT=8000
export API_HOST="0.0.0.0"
```

### Configuration Files
- `.env` - Environment variables (not in git)
- `server/config.py` - Server configuration
- `server/web/.env.local` - Frontend config

## Security Considerations

### API Security
- API key authentication required
- Rate limiting enabled
- CORS configuration for allowed origins
- Input validation on all endpoints

### Ngrok Security
- Use authentication token
- Enable basic auth for public tunnels
- Monitor access logs
- Rotate URLs regularly

### Data Security
- No sensitive data in public repos
- Database encryption at rest
- Secure credential storage
- Regular security audits

## Monitoring & Logs

### Application Logs
```bash
# Backend logs
tail -f server/logs/api.log

# OCR processing logs
tail -f logs/ocr_house_oversight.log
```

### Performance Monitoring
- API response times
- Database query performance
- Memory usage
- CPU utilization

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database status
curl http://localhost:8000/api/status
```

## Backup & Recovery

### Database Backups
```bash
# Backup KuzuDB
tar -czf kuzu_backup_$(date +%Y%m%d).tar.gz data/kuzu_db/

# Backup metadata
cp -r data/metadata/ backups/metadata_$(date +%Y%m%d)/
```

### Recovery Procedures
1. Stop running services
2. Restore database from backup
3. Verify data integrity
4. Restart services
5. Run health checks

## Troubleshooting

### Common Issues

#### API Won't Start
```bash
# Check port availability
lsof -i :8000

# Check Python dependencies
pip list | grep fastapi
```

#### Ngrok Connection Failed
```bash
# Verify ngrok installation
ngrok version

# Check authentication
ngrok authtoken [your-token]
```

#### Database Connection Error
```bash
# Check database path
ls -la data/kuzu_db/

# Verify permissions
chmod -R 755 data/kuzu_db/
```

## Scaling

### Horizontal Scaling
- Load balancer configuration
- Multiple API instances
- Shared database access
- Cache layer (Redis)

### Vertical Scaling
- Increase worker processes
- Optimize database queries
- Add caching
- Upgrade server resources

## Updates & Maintenance

### Deployment Process
1. Test changes locally
2. Run full test suite
3. Create backup
4. Deploy to production
5. Verify deployment
6. Monitor for issues

### Rolling Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt
cd server/web && npm install

# Restart services
systemctl restart epstein-api
```

## Related Documentation

- [Developer Documentation](../developer/README.md) - Development guides and API docs
- [Data Documentation](../data/README.md) - Data structures and processing
- [Main Documentation Index](../README.md) - Complete documentation index

## Support

### Getting Help
1. Check this documentation
2. Review [Developer Documentation](../developer/README.md)
3. Check [Bug Fixes](../developer/BUG_FIXES.md)
4. Create issue on project repository

### Contact Information
See project README for contribution guidelines and contact information.

---

**Last Updated**: 2025-11-17
**Maintained By**: Operations Team
