# Contributing to Multi-Platform Spam Moderator

Thank you for considering contributing to this project! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs if applicable
- **Screenshots** if relevant

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Clear use case** for the enhancement
- **Detailed description** of the proposed functionality
- **Examples** of how it would work
- **Potential challenges** or concerns

### Adding Platform Support

Want to add support for a new platform?

1. Check if the platform has an official API
2. Create a new adapter file in `src/` (e.g., `platform_adapter.py`)
3. Follow the pattern from existing adapters
4. Add configuration options in `config/config.example.env`
5. Update documentation
6. Add tests

### Improving Detection

Improvements to spam detection are always welcome:

1. Add new keywords to `src/core_detector.py`
2. Improve pattern recognition
3. Enhance confidence scoring
4. Add new detection methods
5. Include test cases

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Setup Steps

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/judol-delet-msg.git
cd judol-delet-msg
```

2. **Create virtual environment**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Create configuration**

```bash
copy config\config.example.env .env
# Edit .env with your test credentials
```

5. **Run tests**

```bash
python tests\test_all.py
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise
- Use type hints where appropriate

### Example

```python
def moderate_comments(
    self,
    comments: List[Dict],
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Moderate a list of comments for spam.
    
    Args:
        comments: List of comment dictionaries
        dry_run: If True, don't actually delete spam
        
    Returns:
        Dict with moderation statistics
    """
    # Implementation here
    pass
```

### Documentation

- Keep documentation up to date
- Use clear, concise language
- Include code examples
- Update README.md for major changes
- Add entries to CHANGELOG.md

### Testing

- Write tests for new features
- Ensure existing tests pass
- Test with dry run mode first
- Verify with real data when possible

## Commit Guidelines

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(instagram): add story comment moderation

- Adds support for moderating story comments
- Includes rate limiting
- Updates documentation

Closes #123
```

```
fix(detector): improve typo variant detection

The typo detection was missing common variations
like "sl0t" and "gac0r". This fix adds better
normalization.
```

```
docs(readme): update installation instructions

- Clarify Python version requirements
- Add troubleshooting section
- Fix broken links
```

## Pull Request Process

### Before Submitting

1. **Update your fork**

```bash
git remote add upstream https://github.com/original/judol-delet-msg.git
git fetch upstream
git checkout master
git merge upstream/master
```

2. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

3. **Make your changes**

- Write clear, documented code
- Add tests
- Update documentation
- Test thoroughly

4. **Commit your changes**

```bash
git add .
git commit -m "feat(scope): description"
```

5. **Push to your fork**

```bash
git push origin feature/your-feature-name
```

### Creating the Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Address feedback** if requested
4. **Approval** and merge

### After Merge

- Delete your feature branch
- Update your local master
- Celebrate! 🎉

## Additional Notes

### Adding Dependencies

If you need to add a new dependency:

1. Add it to `requirements.txt`
2. Explain why it's needed in the PR
3. Consider the impact on users

### Breaking Changes

If your change is breaking:

1. Mark it clearly in commit message
2. Update version number (major version)
3. Provide migration guide
4. Update CHANGELOG.md

### Documentation

Good documentation is crucial:

- Update `docs/README.md` for detailed changes
- Update main `README.md` for major features
- Add examples to `docs/CARA_MENCOBA.md`
- Keep `STRUCTURE.md` current

## Questions?

Feel free to:

- Open an issue for questions
- Join discussions
- Ask for clarification

## Recognition

Contributors will be recognized in:

- CHANGELOG.md
- README.md contributors section
- Release notes

---

**Thank you for contributing!** 🙏

Your time and effort help make this project better for everyone.
