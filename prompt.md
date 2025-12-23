# AI Story Album Conversation Summary

## Project Trajectory
- Initial repo used Streamlit; spec in `project.md` expanded to modular architecture with Vue frontend + FastAPI backend.
- Backend now exposes `/api/analyze`, `/api/story`, `/api/export` (PDF) and handles multi-image inputs, BLIP/DeepFace fallbacks, and ReportLab rendering.
- Frontend replaced with Vue 3 + Pinia + Axios, playful blue/orange palette, multi-upload workflow, image overlays, and PDF download flow.

## Key Requirements & Decisions
1. **Motivation & Scope**: Turn static photos into emotional narratives ("From pixels to prose") with local processing and privacy options.
2. **Architecture**: Frontend (Vue/Vite) + Backend (FastAPI, modules for analysis & LLM), message schema includes captions, emotions, tags, color profiles, and story panels.
3. **LLM Integration**: Gemini 2.5 Flash with JSON outputs; fallback text when models unavailable; Traditional Chinese enforcement when language = `zh-TW`.
4. **Story Output**: Multi-photo storybook (panels + summary); text must be overlaid on images both in UI and exported PDF; no plain-text-only output.
5. **Export Format**: PDF only, using ReportLab to embed photos + overlay gradient text blocks.
6. **Frontend UX**: Multi-upload, analysis cards, style/language selectors, user-friendly design, separators between tags using `/`.
7. **Testing Notes**: Running requires `GOOGLE_API_KEY`, optional `ENABLE_DEEPFACE`; install `reportlab` via updated `requirements.txt`; BLIP fallback handles missing torch >=2.6.

## Outstanding Considerations
- BLIP may still need safetensors or torch >=2.6; document upgrade path.
- Potential future tasks: composer themes, queueing, IoT integration per `project.md` roadmap.

Use this prompt to re-derive the current system goals, requirements, and implementation context.
