# Contributing to GIMP AI Integration

Thank you for your interest in contributing to the GIMP AI Integration project! This document outlines the process for contributing to the project and how you can help make it better.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to example@example.com.

## How Can I Contribute?

There are many ways to contribute to the GIMP AI Integration project:

### Reporting Bugs

- Check the [GitHub Issues](https://github.com/yourusername/gimp-ai-integration/issues) to see if the bug has already been reported
- If not, create a new issue using the Bug Report template
- Include detailed steps to reproduce the issue
- Include your system information (OS, GIMP version, etc.)
- Include screenshots or error messages if applicable

### Suggesting Features

- Check the [GitHub Issues](https://github.com/yourusername/gimp-ai-integration/issues) to see if the feature has already been suggested
- If not, create a new issue using the Feature Request template
- Describe the feature in detail and explain how it would benefit users
- Include mockups or examples if possible

### Contributing Code

1. **Fork the repository**
2. **Clone your fork**
   ```
   git clone https://github.com/your-username/gimp-ai-integration.git
   cd gimp-ai-integration
   ```
3. **Create a new branch**
   ```
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes**
   - Follow the [code style guidelines](#code-style)
   - Add tests for your changes when possible
   - Update documentation as needed
5. **Commit your changes**
   ```
   git commit -m "Description of your changes"
   ```
6. **Push to your fork**
   ```
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**
   - Go to your fork on GitHub and click the "New Pull Request" button
   - Select your branch and submit the pull request
   - Include a clear description of your changes
   - Reference any related issues

### Improving Documentation

- Fix typos or clarify existing documentation
- Add examples or tutorials
- Translate documentation to other languages

## Development Setup

1. **Prerequisites**
   - Python 3.8 or later
   - GIMP 2.10 or later
   - Git

2. **Clone the repository**
   ```
   git clone https://github.com/yourusername/gimp-ai-integration.git
   cd gimp-ai-integration
   ```

3. **Create a virtual environment**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

5. **Check environment**
   ```
   python scripts/check_environment.py
   ```

6. **Install the plugin**
   ```
   python scripts/deploy.py
   ```

7. **Run the MCP server**
   ```
   python backend/server/app.py
   ```

## Code Style

This project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use the following tools to maintain code quality:

- **Black**: For code formatting
- **isort**: For import sorting
- **flake8**: For linting

To ensure your code follows the style guidelines, run:
```
black backend frontend
isort backend frontend
flake8 backend frontend
```

## Testing

We use pytest for testing. To run tests:
```
pytest backend/tests
```

Please ensure your code passes all tests before submitting a pull request.

## AI Model Contributions

If you want to contribute a new AI model:

1. Add the model implementation to `backend/server/models/`
2. Add a handler for the model in `backend/server/handlers/`
3. Register the handler in `backend/server/routes/json_rpc.py`
4. Create a dialog for the model in `frontend/gimp_plugin/dialogs/`
5. Add the dialog to `frontend/gimp_plugin/plugin_main.py`
6. Update documentation to include the new model

## Documentation

Update documentation as needed when adding new features or fixing bugs. Documentation is written in Markdown and stored in the `docs/` directory.

## Release Process

The release process is managed by the core team. If you're interested in helping with releases, please contact us.

## Questions?

If you have any questions or need help with contributing, please create an issue on GitHub or contact us at example@example.com.

Thank you for your contributions!
