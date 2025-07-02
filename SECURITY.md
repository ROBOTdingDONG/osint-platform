# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| 0.9.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Private Disclosure
1. **Do NOT** create a public GitHub issue
2. Email security@osintplatform.com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Your contact information

### What to Expect
- **Initial Response**: Within 48 hours
- **Status Update**: Weekly updates on progress
- **Resolution Timeline**: 90 days maximum for critical issues

### Responsible Disclosure
- Give us reasonable time to fix the issue
- Don't access or modify user data
- Don't perform destructive testing

## Security Measures

### Data Protection
- All data encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- Regular security audits
- GDPR compliance

### Authentication & Authorization
- JWT with short expiration
- Multi-factor authentication support
- Role-based access control
- Session management

### Infrastructure Security
- Regular dependency updates
- Container security scanning
- Network isolation
- Monitoring and alerting

## Bug Bounty

We currently don't have a formal bug bounty program, but we recognize security researchers who responsibly disclose vulnerabilities:

- Hall of Fame recognition
- Swag and merchandise
- Direct communication with our security team

## Contact

- Security Team: security@osintplatform.com
- PGP Key: [Link to public key]