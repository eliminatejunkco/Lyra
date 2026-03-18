# Lyra — AI Prompt Optimizer

Lyra is a master-level AI prompt optimizer that transforms rough ideas into powerful, platform-specific prompts for ChatGPT, Claude, Gemini, and others using the **4-D Method**.

## Live Demo

Open `index.html` in any modern browser — no build step required.

## Features

- **4-D Method**: Deconstruct → Diagnose → Develop → Deliver
- **Two modes**
  - `DETAIL` — asks 3 clarifying questions before delivering a fully optimized prompt
  - `BASIC` — instant optimization, ready to use immediately
- **Platform-aware** optimization for ChatGPT, Claude, Gemini, and generic targets
- **Optimization techniques**: role framing, task decomposition, context layering, chain-of-thought, few-shot examples, multi-perspective framing, constraint targeting
- **Structured response**: Optimized Prompt · What Changed · Techniques Applied · Pro Tip

## Project Structure

```
index.html   — application shell & chat UI
styles.css   — modern dark-theme styling
lyra.js      — Lyra engine (4-D Method, modes, optimization logic)
```

## Usage

1. Open `index.html` in a browser.
2. Tell Lyra your **target AI** (e.g. ChatGPT, Claude) and your preferred **mode** (DETAIL or BASIC).
3. Paste or type your rough prompt.
4. Receive an optimized prompt along with explanation notes.

## The 4-D Method

| Step | Description |
|------|-------------|
| **Deconstruct** | Identify core intent, key entities, constraints, and missing context |
| **Diagnose** | Spot clarity issues, fill gaps, assess structure and complexity |
| **Develop** | Choose strategy (creative / technical / educational / complex), assign role, structure logic, optimize output style |
| **Deliver** | Format the optimized prompt and add improvement notes or usage tips |