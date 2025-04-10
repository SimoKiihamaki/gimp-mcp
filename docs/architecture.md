# Architecture Overview

This document provides a high-level overview of the GIMP AI Integration architecture, detailing how the components interact and how data flows through the system.

## System Components

The GIMP AI Integration consists of two main components:

1. **GIMP Python Plugin (Frontend)**
   - Integrates with GIMP's menu system and UI
   - Provides user interfaces for AI features
   - Sends requests to the MCP server
   - Applies results back to GIMP layers/images

2. **MCP Server (Backend)**
   - Implements JSON-RPC endpoints
   - Handles image processing requests
   - Interfaces with AI models
   - Returns processed images/data to the plugin

## Data Flow

```
 ┌────────────┐
 │  User      │
 │ (GIMP)     │
 └─────┬──────┘
       │
       ▼
 ┌────────────┐
 │Select AI    │
 │Feature from │
 │Menu         │
 └─────┬──────┘
       │
       │ (1) Gather Context & Params
       ▼
 ┌───────────────────┐
 │Display Config/Prompt│
 │Dialog in GIMP      │
 └─────┬──────────────┘
       │ (2) Confirm & Invoke
       ▼
 ┌───────────────────┐
 │  GIMP Python      │
 │  Plugin           │
 └─────┬─────────────┘
       │ (3) Send JSON-RPC
       ▼
 ┌───────────────────┐
 │     MCP Server    │
 │(Processing & AI)  │
 └─────┬─────────────┘
       │ (4) AI Model Ops
       ▼
 ┌───────────────────┐
 │ AI Model /        │
 │ External Service  │
 └─────┬─────────────┘
       │ (5) Return Results
       ▼
 ┌───────────────────┐
 │   MCP Server      │
 └─────┬─────────────┘
       │ (6) JSON-RPC Response
       ▼
 ┌───────────────────┐
 │  GIMP Python      │
 │  Plugin           │
 └─────┬─────────────┘
       │ (7) Apply Results
       ▼
 ┌───────────────────┐
 │  GIMP UI Updates  │
 └───────────────────┘
```

## Communication Protocol

The plugin and server communicate using JSON-RPC 2.0 over HTTP. For long-running tasks, the server may use Server-Sent Events (SSE) to provide progress updates.

Example JSON-RPC request:
```json
{
  "jsonrpc": "2.0",
  "method": "ai_inpainting",
  "params": {
    "image_data": "<base64-encoded-image>",
    "mask_data": "<base64-encoded-mask>",
    "params": {
      "strength": 0.8
    }
  },
  "id": 1
}
```

## Extensibility

The architecture is designed to be extensible:
- New AI features can be added by creating new handlers on the server
- New UI dialogs can be added to the plugin
- Different AI models can be integrated as needed

For more detailed information on extending the system, see the [Developer Guide](developer_guide.md).
