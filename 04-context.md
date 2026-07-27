Milestone 4 — AI-driven Engineering
🎯 The Challenge
📌 You are building on your own fork of the company's monorepo selected at the beginning of the course — not on a new repository.

You have three milestones behind you: the public website, the business logic in TypeScript, and the first AI-generated components. You have pieces. What you don't have yet is the system that connects them and will grow alongside them.

From this milestone on, the monorepo stops being a collection of separate projects and becomes the technical core of your company. Everything you build from here — APIs, agents, automations — will live in this same space. That's why, before adding more code, you need to build the infrastructure that will make that code coherent, maintainable, and AI-ready.

Your tech lead has had a ticket sitting on the board for two weeks:

Subject: Monorepo AI Setup — we need this done this week

Hi,

I've reviewed the state of the repo and we're accumulating code without any supporting structure. If I drop an agent on this right now it's going to make mistakes that will cost us triple the time to fix.

I need the repository to have clear, persistent context before we keep adding features: what the company is, what we're building, what the project rules are. That goes into the memory bank. The agent has to read it before touching anything — and it has to include both business context and technical context, not just one of the two.

I also want an AGENTS.md that defines how any agent operates in this repo — what workflow it has to follow before making a commit. No agents writing code without going through the delivery process.

For more specific rules we'll use the .agents/ folder. Think about what conventions the agent needs to know to not break what we already have, and document them there with the correct scope.

Finally, I want us to formalise at least one skill that captures a recurring task in our workflow — something the agent can execute consistently and that we can reuse in upcoming milestones. It needs explicit acceptance criteria: if it can't be verified, it doesn't count.

As for the app, the public website needs to live in ./uis/website as a Next.js app — not as a copy, but as an improved version with reusable components. In parallel, create ./uis/backoffice to host all internal company logic with its own layout and entry view, and integrate the TypeScript script from the business logic module (Milestone 2) there so we have something visible from day one. Any APIs must be created under /services.

When you're done, open a PR and let me know.

— [Your tech lead]

💡 Memory bank, rules, and skills: what they are and why they matter
A memory bank is a set of Markdown files that the coding agent reads before each session. It is not static documentation — it is the active context of the project: business description, architectural decisions made, active constraints, and the current state of development. Without it, every agent session starts from scratch and repeats the same mistakes. That's why the memory bank must be updated every time the project evolves: new decisions, architecture changes, completed features, problems encountered. A memory bank that isn't kept up to date stops being useful within days. Never forget this!

The expected structure for agent configuration in the monorepo is the following:

./.agents
└─ /rules
   └─ <rule-name>.md
└─ /skills
   └─ /<skill>
      └─ SKILL.md
./memory-bank
└─ <context>.md
⚠️ Attention: Do not confuse .agents/ with the /agents and /skills folders you will see in the monorepo. .agents/ is the configuration directory for coding agents (Cursor, Windsurf, Claude Code…) — this is where the rules and skills that teach the agent how to work in this repository go. The /agents and /skills folders are for the agents and integrations you will build for the company starting in later milestones. They are different things: one configures how your development tool works, the other is product code.

Before creating any new folder, review the README.md inside each folder of the monorepo — the template repository includes instructions on what should go in each space. Following them will prevent duplication and keep a structure the agent can navigate without ambiguity.

Development rules (AGENTS.md and .agents/rules/) are the protocol the agent follows automatically: what to read at the start, what steps are mandatory before each commit, which conventions to respect, and when to stop and ask. They act as the team agreement that ensures the agent doesn't make decisions on its own where it shouldn't.

An agent skill is a structured, reusable instruction: more concrete than a generic rule, with defined inputs, expected output, and verifiable acceptance criteria. A good skill has a single objective and can be tested independently.