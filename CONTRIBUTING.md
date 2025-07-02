# Contributing to OSINT Platform

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a positive environment

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/osint-platform.git
   ```
3. **Set up development environment**
   ```bash
   ./scripts/setup.sh
   ```

## Development Workflow

### Branch Naming Convention
- `feature/description` - New features
- `bugfix/description` - Bug fixes  
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat(api): add competitor analysis endpoint

- Add new endpoint for competitor data analysis
- Include sentiment scoring and trend detection
- Add comprehensive test coverage

Closes #123
```

## Code Standards

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for all functions
- Minimum 80% test coverage
- Use Black for code formatting
- Use isort for import sorting

```python
def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of given text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Sentiment score between -1.0 and 1.0
    """
    # Implementation here
    pass
```

### TypeScript (Frontend)
- Use TypeScript strict mode
- Follow Prettier configuration
- Use ESLint rules
- Prefer functional components with hooks

```typescript
interface DataPoint {
  id: string;
  source: string;
  content: string;
  timestamp: Date;
  sentiment?: number;
}

const DataCard: React.FC<{ data: DataPoint }> = ({ data }) => {
  // Implementation here
};
```

## Testing Requirements

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

### Frontend Tests
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md**
5. **Create pull request** with:
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes

### PR Template
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Breaking changes documented
- [ ] Security implications considered

## Issue Guidelines

### Bug Reports
Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error logs/screenshots

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## Security

Report security vulnerabilities privately to security@osintplatform.com. Do not create public issues for security problems.

## Questions?

- Join our Discord: [Community Link]
- Email: dev@osintplatform.com
- Documentation: [Docs Link]