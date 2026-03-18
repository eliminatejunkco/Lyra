/* =========================================================
   Lyra — AI Prompt Optimizer  |  lyra.js
   ========================================================= */

"use strict";

// ── Constants ────────────────────────────────────────────

const PLATFORMS = {
  chatgpt:  { label: "ChatGPT",  note: "Use clear role starters and structured task decomposition." },
  claude:   { label: "Claude",   note: "Leverage long-context depth and detailed reasoning chains." },
  gemini:   { label: "Gemini",   note: "Use comparative framing and creative multi-angle prompts." },
  gpt4:     { label: "GPT-4",    note: "Use clear role starters and structured task decomposition." },
  other:    { label: "AI",       note: "Apply core prompt engineering principles." },
};

const TECHNIQUES = {
  roleFraming:       "Role framing",
  taskDecomposition: "Task decomposition",
  contextLayering:   "Context layering",
  chainOfThought:    "Chain-of-thought",
  fewShot:           "Few-shot examples",
  multiPerspective:  "Multi-perspective framing",
  constraintTarget:  "Constraint targeting",
  outputSpec:        "Output format specification",
};

const PRO_TIPS = [
  "Paste this into a new conversation — avoid building on long contexts that may dilute focus.",
  "If the output is too long, append: 'Reply in under N words.'",
  "Iterate: after the first response, ask the AI to 'improve section 3 specifically.'",
  "Save your optimized prompt as a template for similar future tasks.",
  "Run the same prompt on 2–3 platforms and compare responses for richer insight.",
  "For complex tasks, split into sequential prompts rather than one mega-prompt.",
];

const DETAIL_QUESTIONS = [
  {
    key: "audience",
    ask: "Who is the **target audience** or end reader for this output? (e.g. beginner, expert, child, professional)",
  },
  {
    key: "format",
    ask: "What **output format** do you need? (e.g. bullet list, essay, step-by-step guide, code snippet, table)",
  },
  {
    key: "tone",
    ask: "What **tone or style** should the response have? (e.g. formal, casual, persuasive, concise, creative)",
  },
];

// ── State ────────────────────────────────────────────────

const state = {
  mode: null,                // "DETAIL" | "BASIC"
  platform: null,            // key from PLATFORMS
  originalPrompt: null,
  detailAnswers: {},
  phase: "welcome",          // welcome → modeSelect → platformSelect → promptInput → detailQA → done
  currentQuestionIndex: 0,
};

// ── DOM refs ─────────────────────────────────────────────

const chatWindow   = document.getElementById("chatWindow");
const userInput    = document.getElementById("userInput");
const sendBtn      = document.getElementById("sendBtn");
const quickActions = document.getElementById("quickActions");

// ── Boot ─────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  initModeButtons();
  bindInput();
  showWelcome();
});

function initModeButtons() {
  quickActions.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      handleModeSelect(mode);
    });
  });
}

function bindInput() {
  // auto-resize textarea
  userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 160) + "px";
  });

  sendBtn.addEventListener("click", handleSend);

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
}

// ── Welcome ──────────────────────────────────────────────

function showWelcome() {
  const html = `
    <p>Hello! I'm <strong>Lyra</strong>, your AI prompt optimizer. I turn rough ideas into powerful prompts.</p>
    <p style="margin-top:8px">Tell me your:</p>
    <ul style="margin:8px 0 0 18px; line-height:2">
      <li><strong>Target AI</strong> (e.g. ChatGPT, Claude, Gemini)</li>
      <li><strong>Style</strong>: <em>DETAIL</em> (I'll ask questions) or <em>BASIC</em> (quick fix)</li>
    </ul>
    <p style="margin-top:10px" class="text-muted">Select a mode below, or just describe your prompt and I'll get started.</p>
  `;
  appendLyraMessage(html);
  state.phase = "modeSelect";
}

// ── Mode selection ────────────────────────────────────────

function handleModeSelect(mode) {
  state.mode = mode;
  quickActions.classList.add("hidden");

  appendUserMessage(mode === "DETAIL" ? "DETAIL mode" : "BASIC mode");

  quickActions.querySelectorAll(".mode-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.mode === mode);
  });

  if (mode === "DETAIL") {
    appendLyraMessage(
      "Great — <strong>DETAIL mode</strong> activated. I'll ask a few targeted questions before delivering a fully optimized prompt.<br><br>" +
      "First, which AI platform will you use? (ChatGPT, Claude, Gemini, or other)"
    );
  } else {
    appendLyraMessage(
      "<strong>BASIC mode</strong> activated — I'll deliver an optimized prompt right away.<br><br>" +
      "Which AI platform will you use? (ChatGPT, Claude, Gemini, or other)"
    );
  }
  state.phase = "platformSelect";
}

// ── Input dispatcher ──────────────────────────────────────

function handleSend() {
  const text = userInput.value.trim();
  if (!text) return;
  appendUserMessage(text);
  userInput.value = "";
  userInput.style.height = "auto";

  switch (state.phase) {
    case "modeSelect":
      detectModeFromText(text);
      break;
    case "platformSelect":
      handlePlatformInput(text);
      break;
    case "promptInput":
      handlePromptInput(text);
      break;
    case "detailQA":
      handleDetailAnswer(text);
      break;
    case "done":
      handleFollowUp(text);
      break;
    default:
      detectModeFromText(text);
  }
}

// ── Phase: mode detection from free text ─────────────────

function detectModeFromText(text) {
  const up = text.toUpperCase();
  if (up.includes("DETAIL")) {
    handleModeSelect("DETAIL");
  } else if (up.includes("BASIC")) {
    handleModeSelect("BASIC");
  } else {
    // No mode mentioned — treat it as a platform or prompt and default to BASIC
    state.mode = "BASIC";
    quickActions.classList.add("hidden");
    handlePlatformInput(text);
  }
}

// ── Phase: platform detection ─────────────────────────────

function handlePlatformInput(text) {
  const up = text.toUpperCase();
  if (up.includes("CLAUDE"))       state.platform = "claude";
  else if (up.includes("GEMINI"))  state.platform = "gemini";
  else if (up.includes("GPT-4") || up.includes("GPT4")) state.platform = "gpt4";
  else if (up.includes("CHATGPT") || up.includes("GPT")) state.platform = "chatgpt";
  else                              state.platform = "other";

  const platformLabel = PLATFORMS[state.platform].label;

  withTyping(() => {
    appendLyraMessage(
      `Got it — optimizing for <strong>${platformLabel}</strong>.<br><br>` +
      "Now paste or type the prompt you'd like me to optimize:"
    );
    state.phase = "promptInput";
  });
}

// ── Phase: receive prompt ─────────────────────────────────

function handlePromptInput(text) {
  state.originalPrompt = text;

  if (state.mode === "DETAIL") {
    state.currentQuestionIndex = 0;
    withTyping(() => {
      appendLyraMessage(
        "Thanks! Before I optimize, let me ask a few quick questions to tailor the result.\n\n" +
        buildQuestionBlock()
      );
      state.phase = "detailQA";
    });
  } else {
    withTyping(() => {
      deliverOptimizedPrompt();
      state.phase = "done";
    }, 900);
  }
}

// ── Phase: detail Q&A ────────────────────────────────────

function buildQuestionBlock() {
  const html = `<div class="question-block">` +
    DETAIL_QUESTIONS.map((q, i) =>
      `<div class="question-item">
        <div class="q-num">${i + 1}</div>
        <div class="q-text">${q.ask}</div>
      </div>`
    ).join("") +
    `</div><p style="margin-top:10px" class="text-muted">Answer all three in one message (separated by commas or new lines), or answer them one at a time.</p>`;
  return html;
}

function handleDetailAnswer(text) {
  const lines = text.split(/[\n,]+/).map((l) => l.trim()).filter(Boolean);

  // Map answers to questions by position
  DETAIL_QUESTIONS.forEach((q, i) => {
    if (lines[i]) state.detailAnswers[q.key] = lines[i];
    else if (!state.detailAnswers[q.key]) state.detailAnswers[q.key] = "general";
  });

  withTyping(() => {
    deliverOptimizedPrompt();
    state.phase = "done";
  }, 1000);
}

// ── Phase: follow-up ──────────────────────────────────────

function handleFollowUp(text) {
  const up = text.toUpperCase();

  if (up.includes("AGAIN") || up.includes("NEW") || up.includes("ANOTHER") || up.includes("OPTIMIZE")) {
    withTyping(() => {
      appendLyraMessage(
        "Sure! Paste your next prompt and I'll optimize it right away."
      );
      state.originalPrompt = null;
      state.detailAnswers  = {};
      state.phase = "promptInput";
    });
    return;
  }

  if (up.includes("DETAIL") || up.includes("MORE") || up.includes("QUESTION")) {
    state.mode = "DETAIL";
    state.phase = "promptInput";
    withTyping(() => {
      appendLyraMessage(
        "Switching to <strong>DETAIL</strong> mode. Paste your prompt and I'll ask clarifying questions first."
      );
    });
    return;
  }

  // Treat follow-up text as a new prompt to optimize
  state.originalPrompt = text;
  withTyping(() => {
    deliverOptimizedPrompt();
  }, 900);
}

// ── 4-D Engine ───────────────────────────────────────────

/**
 * STEP 1 — DECONSTRUCT
 * Returns an analysis object with detected intent, missing context, entities, and constraints.
 */
function deconstruct(prompt) {
  const lower = prompt.toLowerCase();

  const hasRole       = /\b(you are|act as|as a|as an|pretend|role of)\b/i.test(prompt);
  const hasAudience   = /\b(beginner|expert|student|professional|child|developer|manager|team)\b/i.test(prompt);
  const hasConstraint = /\b(max|limit|only|without|avoid|no more than|within|must not)\b/i.test(prompt);
  const hasFormat     = /\b(list|table|bullet|step[- ]by[- ]step|essay|paragraph|code|markdown|json|numbered)\b/i.test(prompt);
  const hasTone       = /\b(formal|casual|concise|detailed|friendly|professional|creative|simple)\b/i.test(prompt);
  const hasExample    = /\b(example|e\.g\.|for instance|such as|like this)\b/i.test(prompt);
  const hasPurpose    = /\b(help|explain|write|create|generate|summarize|analyze|compare|review|translate|improve|build|design|plan|list)\b/i.test(prompt);

  // Task type heuristic
  let taskType = "general";
  if (/\b(write|draft|story|poem|creative|blog|essay|article)\b/i.test(prompt)) taskType = "creative";
  else if (/\b(code|function|class|debug|script|api|algorithm|programming|implement)\b/i.test(prompt)) taskType = "technical";
  else if (/\b(explain|teach|learn|understand|what is|how does|tutorial|lesson)\b/i.test(prompt)) taskType = "educational";
  else if (/\b(plan|strategy|analyze|compare|evaluate|decision|pros and cons|research)\b/i.test(prompt)) taskType = "analytical";

  return { hasRole, hasAudience, hasConstraint, hasFormat, hasTone, hasExample, hasPurpose, taskType };
}

/**
 * STEP 2 — DIAGNOSE
 * Returns a list of issues and gaps found.
 */
function diagnose(analysis) {
  const issues = [];
  if (!analysis.hasRole)       issues.push("No expert role defined");
  if (!analysis.hasAudience)   issues.push("Target audience not specified");
  if (!analysis.hasFormat)     issues.push("Output format not specified");
  if (!analysis.hasTone)       issues.push("Tone/style not specified");
  if (!analysis.hasConstraint) issues.push("No length or scope constraints");
  if (!analysis.hasPurpose)    issues.push("Core task verb could be more specific");
  return issues;
}

/**
 * STEP 3 — DEVELOP
 * Builds the optimized prompt from the original + analysis + detail answers.
 */
function develop(original, analysis, detailAnswers, platform) {
  const appliedTechniques = [];
  const changes           = [];
  let   optimized         = original.trim();

  // ── Role framing ──────────────────────────────────────
  if (!analysis.hasRole) {
    const role = pickRole(analysis.taskType);
    optimized = `You are ${role}.\n\n${optimized}`;
    appliedTechniques.push(TECHNIQUES.roleFraming);
    changes.push(`Added expert role: "${role}"`);
  }

  // ── Audience ──────────────────────────────────────────
  const audience = detailAnswers.audience;
  if (audience && audience !== "general" && !analysis.hasAudience) {
    optimized += `\n\nTarget audience: ${audience}.`;
    appliedTechniques.push(TECHNIQUES.contextLayering);
    changes.push(`Added target audience context (${audience})`);
  }

  // ── Output format ─────────────────────────────────────
  const fmt = detailAnswers.format;
  if (fmt && fmt !== "general" && !analysis.hasFormat) {
    optimized += `\n\nPresent your response as a ${fmt}.`;
    appliedTechniques.push(TECHNIQUES.outputSpec);
    changes.push(`Specified output format (${fmt})`);
  } else if (!analysis.hasFormat) {
    const defaultFmt = defaultFormat(analysis.taskType);
    optimized += `\n\n${defaultFmt}`;
    appliedTechniques.push(TECHNIQUES.outputSpec);
    changes.push(`Added default output format guidance`);
  }

  // ── Tone ──────────────────────────────────────────────
  const tone = detailAnswers.tone;
  if (tone && tone !== "general" && !analysis.hasTone) {
    optimized += ` Use a ${tone} tone throughout.`;
    appliedTechniques.push(TECHNIQUES.contextLayering);
    changes.push(`Specified tone/style (${tone})`);
  }

  // ── Chain-of-thought (technical / analytical tasks) ───
  if (["technical", "analytical"].includes(analysis.taskType)) {
    optimized += "\n\nThink through this step by step before providing your final answer.\n";
    appliedTechniques.push(TECHNIQUES.chainOfThought);
    changes.push("Added chain-of-thought instruction");
  }

  // ── Constraint (educational / creative tasks) ─────────
  if (!analysis.hasConstraint && ["educational", "creative"].includes(analysis.taskType)) {
    optimized += " Keep the response clear and appropriately scoped.";
    appliedTechniques.push(TECHNIQUES.constraintTarget);
    changes.push("Added implicit scope constraint");
  }

  // ── Task decomposition (complex prompt) ───────────────
  const wordCount = original.split(/\s+/).length;
  if (wordCount > 30 && !appliedTechniques.includes(TECHNIQUES.taskDecomposition)) {
    optimized = injectDecomposition(optimized, analysis.taskType);
    appliedTechniques.push(TECHNIQUES.taskDecomposition);
    changes.push("Restructured with task decomposition");
  }

  // ── Platform-specific tweak ───────────────────────────
  if (platform === "claude") {
    optimized += "\n\nProvide thorough reasoning. It is okay to be detailed.";
    changes.push("Appended Claude-specific depth instruction");
  } else if (platform === "gemini") {
    optimized += "\n\nWhere helpful, include multiple perspectives or comparisons.";
    changes.push("Appended Gemini-specific comparative framing");
    appliedTechniques.push(TECHNIQUES.multiPerspective);
  }

  // Deduplicate
  const uniqueTechniques = [...new Set(appliedTechniques)];
  return { optimized, changes, techniques: uniqueTechniques };
}

/**
 * STEP 4 — DELIVER
 * Returns the final structured output object.
 */
function deliver(original, analysis, detailAnswers, platform) {
  const { optimized, changes, techniques } = develop(original, analysis, detailAnswers, platform);
  const proTip = PRO_TIPS[Math.floor(Math.random() * PRO_TIPS.length)];
  const platformNote = PLATFORMS[platform]?.note ?? PLATFORMS.other.note;
  return { optimized, changes, techniques, proTip, platformNote };
}

// ── Helpers ───────────────────────────────────────────────

function pickRole(taskType) {
  const roles = {
    creative:   "an expert creative writer and storyteller",
    technical:  "a senior software engineer and technical expert",
    educational:"an experienced educator and curriculum designer",
    analytical: "a strategic analyst with expertise in critical thinking",
    general:    "a knowledgeable expert in the relevant domain",
  };
  return roles[taskType] || roles.general;
}

function defaultFormat(taskType) {
  const formats = {
    creative:   "Structure your response with a clear beginning, middle, and end.",
    technical:  "Provide a concise explanation followed by well-commented code or steps.",
    educational:"Use numbered steps or clearly labeled sections to aid comprehension.",
    analytical: "Present your analysis in clearly labeled sections with a summary at the end.",
    general:    "Organize your response with clear sections and headings where appropriate.",
  };
  return formats[taskType] || formats.general;
}

function injectDecomposition(prompt, taskType) {
  const prefix = {
    technical:   "Break this task into logical subtasks. For each subtask:\n",
    analytical:  "Address each aspect of this task systematically:\n",
    educational: "Cover this topic in a structured way:\n",
    creative:    "Approach this creatively and systematically:\n",
    general:     "Address each part of this task carefully:\n",
  };
  // Only prepend the decomposition hint after the role line if present
  const lines = prompt.split("\n");
  const roleEnd = lines.findIndex((l, i) => i > 0 && l.trim() !== "");
  if (roleEnd > 0) {
    lines.splice(roleEnd, 0, (prefix[taskType] || prefix.general));
    return lines.join("\n");
  }
  return (prefix[taskType] || prefix.general) + prompt;
}

// ── Render ────────────────────────────────────────────────

function deliverOptimizedPrompt() {
  const { original, platform, detailAnswers } = {
    original:      state.originalPrompt,
    platform:      state.platform || "other",
    detailAnswers: state.detailAnswers,
  };

  const analysis = deconstruct(original);
  const result   = deliver(original, analysis, detailAnswers, platform);

  const html = buildResultHTML(result, original);
  appendLyraMessage(html);

  appendLyraMessage(
    "✅ Done! You can copy the optimized prompt above. Want to optimize another prompt? Just paste it in."
  );
}

function buildResultHTML(result, original) {
  const { optimized, changes, techniques, proTip, platformNote } = result;

  const changeItems = changes.length
    ? `<ul class="change-list">${changes.map((c) => `<li>${escHtml(c)}</li>`).join("")}</ul>`
    : `<span class="text-muted">No structural changes needed — prompt was already well-formed.</span>`;

  const techniqueTags = techniques.length
    ? `<div class="tag-list">${techniques.map((t) => `<span class="tag">${escHtml(t)}</span>`).join("")}</div>`
    : `<span class="text-muted">Core clarity improvements only.</span>`;

  return `
    <div class="output-block">
      <div class="output-section">
        <div class="section-label">✦ Optimized Prompt</div>
        <div class="prompt-wrapper">
          <div class="section-content prompt-box" id="optimizedText">${escHtml(optimized)}</div>
          <button class="copy-btn" onclick="copyOptimized()" title="Copy to clipboard">Copy</button>
        </div>
      </div>
      <div class="output-section">
        <div class="section-label">What Changed</div>
        <div class="section-content">${changeItems}</div>
      </div>
      <div class="output-section">
        <div class="section-label">Techniques Applied</div>
        <div class="section-content">${techniqueTags}</div>
      </div>
      <div class="output-section">
        <div class="section-label">💡 Pro Tip</div>
        <div class="section-content">${escHtml(proTip)}</div>
      </div>
      <div class="output-section">
        <div class="section-label">Platform Note</div>
        <div class="section-content text-muted">${escHtml(platformNote)}</div>
      </div>
    </div>
  `;
}

// ── UI helpers ────────────────────────────────────────────

function appendLyraMessage(html) {
  const msg = document.createElement("div");
  msg.className = "message lyra";
  msg.innerHTML = `
    <div class="avatar" aria-hidden="true">✦</div>
    <div class="bubble">${html}</div>
  `;
  chatWindow.appendChild(msg);
  scrollToBottom();
  return msg;
}

function appendUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "message user";
  msg.innerHTML = `
    <div class="avatar" aria-hidden="true">U</div>
    <div class="bubble">${escHtml(text)}</div>
  `;
  chatWindow.appendChild(msg);
  scrollToBottom();
}

function withTyping(callback, delay = 600) {
  const indicator = appendTypingIndicator();
  setTimeout(() => {
    indicator.remove();
    callback();
  }, delay);
}

function appendTypingIndicator() {
  const msg = document.createElement("div");
  msg.className = "message lyra";
  msg.innerHTML = `
    <div class="avatar" aria-hidden="true">✦</div>
    <div class="bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  chatWindow.appendChild(msg);
  scrollToBottom();
  return msg;
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/\n/g, "<br>");
}

// ── Copy-to-clipboard ─────────────────────────────────────

function copyOptimized() {
  const el = document.getElementById("optimizedText");
  if (!el) return;
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector(".copy-btn");
    if (btn) {
      btn.textContent = "Copied!";
      setTimeout(() => { btn.textContent = "Copy"; }, 2000);
    }
  }).catch(() => {
    // Fallback for older browsers
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity  = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  });
}
