# Changelog

All notable changes to the GIMP AI Integration project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-beta] - 2025-04-XX

### Added
- Core AI features:
  - Background removal using U2Net
  - Inpainting with LaMa model
  - Style transfer with multiple pre-trained styles
  - Image upscaling with ESRGAN (2x, 4x, and 8x)
- Model Context Protocol (MCP) server:
  - JSON-RPC API with FastAPI
  - Progress updates via Server-Sent Events (SSE)
  - Authentication and HTTPS support
- GIMP integration:
  - User-friendly dialogs for all AI features
  - Progress indicators during processing
  - Option to create new layers/images with results
- Distribution and packaging:
  - Installation scripts for Windows, macOS, and Linux
  - PyPI package for easy installation
  - Standalone installers
- User feedback system:
  - In-app feedback form
  - Bug reporting mechanism
  - Feature request submission
- Documentation:
  - User guide with feature instructions
  - Developer guide for extending the project
  - Architecture overview
  - API documentation

### Changed
- Initial beta release, no previous changes to document

### Fixed
- Initial beta release, no previous fixes to document
