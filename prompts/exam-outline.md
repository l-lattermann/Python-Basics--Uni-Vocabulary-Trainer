# AI-103 skills measured

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103
(skills measured as of April 16, 2026; page checked 2026-10-20).

Exam: 120 minutes, about 40–60 questions, pass at 700. Question types include
multiple choice, multi-select, build list (ordering), drag and drop, hot area,
case studies and possibly labs. Python is the only SDK language named.
Microsoft Learn is open during the exam, so time matters more than recall of
long reference tables.

## plan — Plan and manage an Azure AI solution (25–30%)

- Choose Foundry services: models (LLM, SLM, multimodal, Foundry Tools); services for grounding, vector search and workflows; retrieval and indexing method; agent memory, tools and knowledge.
- Set up: infrastructure design, deployment options, model and agent deployments, CI/CD integration.
- Manage, monitor and secure: quotas, scaling, rate limits and cost; drift, safety events, grounding quality; index health and relevance; managed identity, private networking, keyless credentials, roles.
- Responsible AI: content filters, guardrails, moderation; evaluators and safety evaluations; trace logging, provenance, approval workflows; oversight modes and tool-access controls.

## genai — Implement generative AI and agentic solutions (30–35%)

- Generative apps: deploy and consume LLM, SLM, code and multimodal models; RAG; multistep pipelines; evaluation (fabrication, relevance, safety); SDKs and connectors; connect an app to a Foundry project.
- Agents: roles, goals, tool schemas; retrieval, function calling, memory; tool integration; multi-agent orchestration; autonomous flows with approval controls; monitoring and error analysis.
- Optimize: prompts and parameters; reflection, chain-of-thought, self-critique loops; tracing, token analytics, latency; hybrid LLM plus rules engines.

## vision — Implement computer vision solutions (10–15%)

- Image and video generation, including inpainting, mask edits, editing generated video.
- Multimodal understanding: captions, visual question answering, alt text, Content Understanding (including pro mode), video segments, object and region detection.
- Responsible AI for images: unsafe-image filters, prompt injection hidden in image text, watermarks, brand rules.

## text — Implement text analysis solutions (10–15%)

- Entities, summaries and JSON output via prompting and Foundry Tools; sentiment, tone, sensitive content; Translator or LLM translation; domain customization.
- Speech: speech to text and text to speech for agents, custom speech models, reasoning over audio input, speech translation.

## extraction — Implement information extraction solutions (10–15%)

- Ingest and index documents, images, audio and video; semantic, hybrid and vector search; built-in and custom skills; RAG ingestion with OCR; connect retrieval to agents.
- Content Understanding: OCR, layout and field extraction; structured or Markdown output.
