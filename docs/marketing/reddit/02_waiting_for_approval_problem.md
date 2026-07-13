# The most expensive AI-agent state might be “waiting for approval”

## Body

An agent can appear busy while actually sitting at an approval prompt. If I notice ten minutes later, the model was not the bottleneck—the feedback loop was.

I built a small local dashboard that makes `WAITING_APPROVAL` visible on a Kindle next to my monitor. It also distinguishes RUNNING, IDLE, and STOPPED for Claude Code, Codex, and MiMo Code.

The interesting design constraint was deciding what *not* to show. E-ink is slow, so logs and animations make little sense. A stable status model and a high-contrast layout are much more useful.

Would you prefer one shared approval indicator, or a separate state for each agent?

Project demo: https://baobateer-arch.github.io/AI-Workstation/

## Tags

agent UX, human in the loop, e-ink dashboard, AI workflow, developer productivity

## Image suggestion

A close-up centered on the WAITING_APPROVAL state, plus a simple agent-to-human feedback-loop diagram.
