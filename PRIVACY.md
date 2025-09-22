# Privacy & Security Policy

## Data Handling

### What We Scan
- Source code files
- Configuration files
- Environment files
- Documentation

### What We Don't Store
- Raw secret values
- Personal information
- Code content beyond metadata
- User credentials (except hashed authentication)

### Secret Masking
All detected secrets are automatically masked using the following pattern:
- First 4 characters visible
- Last 4 characters visible
- Middle section replaced with asterisks

Example: `ghp_1234***********5678`

### Data Retention
- Scan results: 24 hours maximum
- Uploaded files: Deleted immediately after scanning
- User sessions: 1 hour JWT expiration
- Logs: Minimal, no sensitive data

### Security Measures
- JWT-based authentication
- Input validation and sanitization
- Secure file handling with automatic cleanup
- Rate limiting on API endpoints
- OWASP security guidelines compliance

### GDPR Compliance
- Minimal data collection
- No personal data retention
- Right to data deletion (automatic)
- Transparent processing

## Reporting Security Issues

Email: security@secrethawk.example.com