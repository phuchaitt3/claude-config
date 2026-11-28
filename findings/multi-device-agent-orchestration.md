---
topic: multi-device-agent-orchestration
area: Agent setup
question: Is it normal to run Claude Code agents on several devices (for example a laptop and a desktop PC), and what is the standard setup for the devices?
checked: 2026-11-28
review_months: 6
status: current
---

# Running Claude Code agents on several devices

**Question:** Is it normal to orchestrate Claude agents across more than one device, and what is the standard device setup?

**Finding:**

- **Normal, but as independent sessions per machine, not one orchestrator driving all.** No source describes a standard in which one controller schedules agents across devices. What the sources describe is each machine running its own Claude Code sessions, with git and the vendor's remote features linking them.
- **Official building blocks (vendor docs):**
  - Remote Control: a session runs on one machine, and claude.ai/code or the phone app is a window into it. "Your computer has to stay on and the `claude` process has to keep running." The local session makes outbound HTTPS requests only and opens no inbound ports. It needs a claude.ai sign-in (Pro, Max, Team, Enterprise); API keys, Bedrock, Vertex, Foundry and custom base URLs are not supported. `claude remote-control` runs a server with `--capacity <N>` concurrent sessions (default 32) and `--spawn worktree` gives each session its own git worktree (default `same-dir` lets sessions conflict).
  - Cross-session messaging: a session connected to Remote Control can list and message "your sessions on other machines" through Anthropic's servers (`ListAgents`, `SendMessage`, `/list-agents`). Needs Claude Code 2.1.224 or later (2.1.234 or later on native Windows; 2.1.225 or later to start a conversation with another machine's session) and a claude.ai sign-in. A message to an offline session arrives when that machine reconnects. Cloud sessions cannot reply by `SendMessage`; some messages are one-way; long reply chains can be cut off. WSL 2 and containers cannot reach a native Windows session on the same computer.
  - Agent teams (experimental): documented as one local setup. Teams and mailboxes are stored locally (`~/.claude/teams/...`), one team per session, a team cannot be shared across sessions. The page never mentions several machines. A feature request for cross-machine teams over a LAN exists, which suggests it is not built (inference from the request's existence).
- **Remote Control on for every session (`/config` "Enable Remote Control for all sessions", `remoteControlAtStartup`), checked 2026-11-23:**
  - Cost and security (official docs, as summarised by search): no inbound ports, outbound HTTPS only, short-lived scoped credentials. Each session allows one remote connection at a time; starting an ultraplan session disconnects Remote Control. Setting `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `CLAUDE_CODE_DISABLE_FEATURE_FLAGS` makes it unavailable. Team and Enterprise: off until an admin enables it. A session offline about 10 minutes times out and the process exits. Docs and third-party guides treat the session URL or QR code as an access key (one guide notes no two-factor on session links). The docs state no token or quota cost for having it on; none found.
  - Reliability (community issue reports, anecdotal, several filed 2026): the link can drop silently while the local terminal keeps running and need `/remote-control` again; auto-reconnect after a network break or long idle is reported not to work in some cases; one report of duplicate messages. A permission prompt appears on the host and can stall a session nobody is watching (a blog's advice: pre-approve permissions first). Docs and issues disagree on how reliable reconnect is.
  - The always-on setting gives no hidden fee found; its costs are the extra network connection per session, exposure of every session to your claude.ai account (a stolen login or leaked link reaches all of them), and unreliable reconnects. Weighing these for a personal setup is the checker's inference.
- **Common community setup (individual blogs, anecdotal):** each machine holds a full clone of a git repository of notes, rules or config; a session-end hook or timer commits and pushes; one place is the source of truth ("one home per fact"); secrets stay out of the synced repository. One author uses the desktop by day and the laptop at night rather than splitting tasks. A reader comment names merge conflicts from concurrent edits on two machines as the main risk.
- **Coordination between machines (inference, not found stated for two machines):** the single-machine multi-agent advice transfers: one task, one branch, one worktree, one session; a shared task list or explicit claims for who owns what; serialised merges. Sources on parallel agents (several blogs) say git isolates files but a task list or claims is needed for work allocation. Nothing found covers splitting tasks across two computers.

## Update 2026-11-27: two machines on one repository

- **Not covered by sources found.** A search for two computers working on one repository with coding agents returned advice about worktrees on one machine only. Those guides say: one task per branch and worktree, split by feature area, and git does not catch collisions in shared databases or ports (blogs). Worktrees do not span computers.
- **A self-hosted CI runner as the second machine's job queue is advised against for public repositories** (blogs): a pull request from anyone could run code on the machine. For private repositories it is described as reasonable for GPU access.
- **Inference (checker's):** using two machines on one repository is ordinary git use and is safe at the git level with one branch per machine. The extra cost is state git does not carry: downloaded inputs, data caches without a remote, local models, container images, and different GPU capability. So give the second machine only tasks whose inputs come from git, a data remote or a fetch script and whose hardware it meets; keep a chain of dependent tasks on one machine; name the machine on the task claim. If most tasks fail that test, one machine plus a cloud GPU is simpler.

Sources for this update:

- [Git worktrees for parallel AI agents](https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution) (vendor blog, search summary only)
- [Multiple AI coding agents, same repository](https://dev.to/robat_das_3c6e956212f6408/multiple-ai-coding-agents-same-repository-the-bugs-git-won-43fb) (individual blog, search summary only)
- [Self-hosted runners: security, scaling and isolation](https://infra.furybee.org/articles/github-actions-self-hosted-runners/) (individual blog, search summary only)

## Update 2026-11-27: routing, claims, data and scaling across machines

**Sourced:**

- **Capability routing is the usual way to send work to the right machine** (official docs): GitHub Actions routes a job by `runs-on` labels, and a self-hosted runner must carry all of them; Kubernetes places a Pod only on nodes with the labels its `nodeSelector` names (read as a summary).
- **A self-hosted runner is not a safe queue for a public repository** (official docs): GitHub says such runners "should almost never be used for public repositories", because a pull request can compromise the machine.
- **Sessions:** cross-session messaging reaches sessions that already exist; the page describes no way to start one on another machine, and a received message never counts as the user's consent (official docs). Remote Control server mode (`claude remote-control`) waits for remote connections (official docs); one blog says the phone app can then start a session on that machine (not confirmed in the docs part read). No start-at-boot setting was found.
- **Queues across a few home machines** (project READMEs): task spooler works on one machine only; `jobd` claims to be a GPU-aware broker across machines on a LAN or Tailscale (young, no independent reports found). Slurm and Ray are described as heavy for two machines; a scheduler is worth it when human coordination fails, not at a set machine count (blogs; no validated threshold).
- **Atomic claims across machines** (project READMEs and issues): some agent task tools use a git ref or a rejected push as the lock, with leases that expire. GitHub's "create a reference" page does not say what happens when the ref already exists, so that route is unverified.
- **Models:** a Hugging Face download is pinned with `revision=` and the full commit hash (official docs). A shared cache over a network mount is possible but has symlink problems between Windows and Linux (official docs and a forum, via search summary).
- **Remote access:** Tailscale's SSH server does not run on Windows; use Windows OpenSSH over the tailnet (guides and an issue, search summary).

**Inference (checker's), for two to a few personal machines:**

- Keep each machine a peer with its own sessions; use the shared services already there (git, the issue tracker, one data remote) and add no controller, queue daemon or shared network drive.
- Record per machine what it has (GPU compute capability and memory, RAM, installed tools) and per task what it needs; check that before claiming. A third machine then adds one record.
- Every input a task needs should be reachable from any machine: git, a data remote, or a download pinned by hash. An export that is generated on request (its bytes change, the service can fail) counts as not re-downloadable and goes in the data remote. Models and container images are downloaded by each machine from the pinned source.
- A label and claim comment on a shared issue tracker is enough while claim collisions are rare; add an atomic lock only after one is seen.

Sources for this update:

- [Using self-hosted runners in a workflow](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow) and [Secure use](https://docs.github.com/en/actions/reference/security/secure-use) (official docs)
- [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) (official docs)
- [Cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging.md), [Remote Control](https://code.claude.com/docs/en/remote-control.md) (official docs); [phone start](https://aicatchup.com/news/claude-code-remote-control-phone-start) (blog, search summary)
- [jobd](https://github.com/musharna/jobd), [task spooler](https://github.com/justanhduc/task-spooler) (project READMEs)
- [Scheduling: Slurm, Kubernetes, Ray, or none](https://kentino.com/pages/job-scheduling-for-ai-clusters-slurm-kubernetes-ray-and-knowing-when-you-need-none-of-them) (vendor page, search summary)
- [tasks.md](https://github.com/tasksmd/tasks.md), [Backlog.md issue 937](https://github.com/MrLesk/Backlog.md/issues/937) (project pages, search summary)
- [Hugging Face download guide](https://huggingface.co/docs/huggingface_hub/en/guides/download) (official docs); [LAN model storage thread](https://discuss.huggingface.co/t/recommended-tools-for-managing-downloading-and-storing-models-on-lan/169112) (forum, search summary)
- [Tailscale SSH to Windows, feature request](https://github.com/tailscale/tailscale/issues/17261) (issue, search summary)

## Update 2026-11-28: does a second machine add throughput on one subscription?

**Sourced:**

- Usage limits belong to the account and are shared by Claude and Claude Code (official help page, search summary). A third-party guide: limits follow the account, not the device, so two computers running at once empty the same 5-hour window about twice as fast (vendor blog, search summary). See also `findings/overnight-agent-runs` and `findings/claude-pro-usage-limits`.
- No vendor statement on throughput from several machines was found, and no measurement.

**Inference (checker's):** on one small plan, a second autonomous run adds finished work only when quota would otherwise go unused before it resets, or when one run spends much of its time waiting on machine-bound jobs. When the weekly limit binds, run the one queue with the most valuable tasks. Splitting by machine is worth it for tasks that need that machine's hardware or data, not to divide the model's work.

Sources for this update:

- [Using Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan) (official help page, search summary)
- [One Claude account on two computers](https://agentsroom.dev/blog/one-claude-account-two-computers-and-two-people) (vendor blog, search summary)

**Evidence strength:** vendor documentation for the Remote Control, messaging and agent-teams facts (official standard for the tool's own behaviour); anecdotal for the sync setup; no data found on how common multi-device setups are or on a standard device split (heavy jobs on the stronger machine is the checker's inference).

**Sources:**

- [Remote Control](https://code.claude.com/docs/en/remote-control.md) (official docs)
- Community issue reports on Remote Control reconnects: [no auto-reconnect after network interruption](https://claudeissues.com/issue/79388-remote-control-does-not-auto-reconnect-after-a-network-interruption), [silent drop, no recovery](https://claudeissues.com/issue/34255-bug-remote-control-automatic-reconnection-doesnt-work-connection-drops-silently), [stability issues](https://claudeissues.com/issue/33205-remote-control-multiple-stability-and-usability-issues-make-autonomous-use-unrel) (seen in search results only, not opened)
- [Cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging.md) (official docs)
- [Agent teams](https://code.claude.com/docs/en/agent-teams.md) (official docs)
- [Feature request: distributed agent teams over a LAN](https://claudeissues.com/issue/79507-feature-distributed-agent-teams-coordinate-claude-code-instances-across-machines) (community issue, seen in search results only, not opened)
- [Keeping Claude Code context alive across a desktop, a laptop and a VPS](https://dev.to/fillip_kosorukov/keeping-claude-code-context-alive-across-a-desktop-a-laptop-and-a-vps-2epa) (individual blog)
- [How to run coding agents across machines](https://www.mindstudio.ai/blog/how-to-run-coding-agents-across-machines) (vendor blog for a third-party terminal tool that works over SSH; not independent, not Claude-specific; 2026-11-08)
- Git worktree guides for parallel agents on one machine (several blogs, seen in search results only)

**Limits:** the docs were read through a summarising fetch tool, so exact wording is partly paraphrase; the Remote Control "Limitations" section was summarised only. Remote Control and messaging are research-preview or fast-changing features. Nothing found on cost or quota use across devices, or on two machines sharing one repository at the same moment beyond the blog comment above.

**Checked:** 2026-11-23
