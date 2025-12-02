# Contributing to F1 WebApp

Thank you for your interest in contributing to F1 WebApp! This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Guidelines](#coding-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences
- Accept responsibility for mistakes

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal attacks
- Publishing private information without permission

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.12 or higher
- Node.js 18 or higher
- uv (Python package manager)
- Git
- Basic knowledge of FastAPI and React

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/f1_webapp.git
   cd f1_webapp
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/f1_webapp.git
   ```

## Development Setup

### Backend Setup

```bash
# Install Python dependencies
uv sync

# Populate the database
uv run python scripts/populate_espn_final.py

# Start the API server
uv run uvicorn src.f1_webapp.api.app:app --reload
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Verify Setup

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:4321

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Update to the latest version
3. Verify the bug is reproducible

**Bug Report Template:**
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., macOS 13.0]
- Python version: [e.g., 3.12.1]
- Node version: [e.g., 18.17.0]
- Browser: [e.g., Chrome 120]

## Additional Context
Screenshots, error logs, etc.
```

### Suggesting Features

**Feature Request Template:**
```markdown
## Feature Description
Clear description of the feature

## Problem It Solves
What problem does this address?

## Proposed Solution
How should this work?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Mockups, examples, etc.
```

### Contributing Code

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the coding guidelines

3. **Test your changes** thoroughly

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Coding Guidelines

### Python (Backend)

**Style Guide:**
- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 100 characters
- Use descriptive variable names

**Example:**
```python
from typing import List, Optional
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/drivers/{driver_id}")
async def get_driver(driver_id: str) -> dict:
    """
    Get driver details by ID.

    Args:
        driver_id: ESPN driver ID

    Returns:
        Driver information dictionary

    Raises:
        HTTPException: If driver not found
    """
    driver = await fetch_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver
```

**Formatting Tools:**
```bash
# Install formatting tools
uv add --dev black ruff isort

# Format code
uv run black src/
uv run isort src/
uv run ruff check src/
```

### TypeScript/React (Frontend)

**Style Guide:**
- Use TypeScript for type safety
- Use functional components with hooks
- Follow React best practices
- Use meaningful component names

**Example:**
```typescript
interface DriverStandingsProps {
  year: number;
  season: string;
}

export function DriverStandings({ year, season }: DriverStandingsProps) {
  const [standings, setStandings] = useState<Standing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStandings(year).then(setStandings).finally(() => setLoading(false));
  }, [year]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="standings-container">
      {standings.map(standing => (
        <StandingRow key={standing.driverId} standing={standing} />
      ))}
    </div>
  );
}
```

**Formatting:**
```bash
# Frontend formatting (uses built-in Astro formatting)
cd frontend
npm run format
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add telemetry comparison endpoint

Add endpoint to compare telemetry data between two drivers
for a specific session.

Closes #123

---

fix(frontend): correct standings calculation for 1950-1959

The points system for early seasons was incorrectly applied.
Now uses historically accurate points allocation.

Fixes #456
```

### Documentation

- Update README.md if adding features
- Add docstrings to all functions
- Update API documentation in docs/
- Include code comments for complex logic
- Update CHANGELOG.md for notable changes

## Testing

### Backend Tests

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio pytest-cov httpx

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/f1_webapp --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test Example:**
```python
import pytest
from fastapi.testclient import TestClient
from src.f1_webapp.api.app import app

client = TestClient(app)

def test_get_driver_standings():
    response = client.get("/espn/standings/2024?type=driver")
    assert response.status_code == 200
    data = response.json()
    assert "standings" in data
    assert len(data["standings"]) > 0

def test_get_invalid_driver():
    response = client.get("/espn/drivers/invalid-id")
    assert response.status_code == 404
```

### Frontend Tests

```bash
cd frontend

# Install test dependencies
npm install --save-dev vitest @testing-library/react

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

**Test Example:**
```typescript
import { render, screen } from '@testing-library/react';
import { DriverStandings } from './DriverStandings';

describe('DriverStandings', () => {
  it('renders loading state initially', () => {
    render(<DriverStandings year={2024} season="2024" />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays standings after loading', async () => {
    render(<DriverStandings year={2024} season="2024" />);
    const firstDriver = await screen.findByText(/verstappen/i);
    expect(firstDriver).toBeInTheDocument();
  });
});
```

## Pull Request Process

### Before Submitting

1. **Update your branch:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests:**
   ```bash
   uv run pytest
   cd frontend && npm test
   ```

3. **Check formatting:**
   ```bash
   uv run black src/ && uv run ruff check src/
   ```

4. **Update documentation** if needed

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] PR description clearly explains changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
```

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, your PR will be merged
4. Your contribution will be credited in CHANGELOG.md

## Project Structure

### Backend Structure
```
src/f1_webapp/
├── api/              # FastAPI application
│   ├── app.py       # Main application
│   └── routes/      # API endpoints
├── espn/            # ESPN client
├── fastf1/          # FastF1 wrapper
└── models/          # Data models
```

### Frontend Structure
```
frontend/
├── src/
│   ├── pages/       # Astro pages (routes)
│   ├── components/  # React components
│   ├── layouts/     # Page layouts
│   └── styles/      # Stylesheets
└── public/          # Static assets
```

### Scripts
```
scripts/
├── populate_espn_final.py    # Main DB population
├── populate_team_logos.py    # Logo scraper
└── README.md                 # Script documentation
```

## Need Help?

- Check existing issues and discussions
- Read the documentation in `/docs`
- Join our Discord community (coming soon)
- Ask questions in GitHub Discussions

## Recognition

Contributors will be:
- Listed in CHANGELOG.md
- Credited in release notes
- Added to CONTRIBUTORS.md (for significant contributions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to F1 WebApp! Your efforts help make F1 data more accessible to everyone.
