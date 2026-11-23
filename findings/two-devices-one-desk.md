---
topic: two-devices-one-desk
area: Agent setup
question: How do people physically use two computers (a laptop and a desktop PC) at the same time at one desk with one keyboard and mouse, and what is the usual way to work on both?
checked: 2026-11-23
review_months: 12
status: current
---

# Using two computers at one desk

**Question:** With a laptop and a desktop PC both running work, is it normal to use a second keyboard and mouse, or is there a standard way to share one set, and how do developers split the work between the two?

**Finding:**

- **Sharing one keyboard and mouse is the usual answer, not two sets.** Three routes appear in the sources:
  - **Software sharing over the network** (Mouse Without Borders, Input Leap, Synergy, Deskflow, ShareMouse): the pointer moves off the edge of one screen onto the other machine's screen, and the clipboard is shared. Each machine keeps its own display, so nothing is switched. Mouse Without Borders is free, Windows-only and part of Microsoft PowerToys. Input Leap and Deskflow are free and open source; Synergy is paid and cross-platform. ShareMouse's free tier is limited to two displays (vendor and comparison-blog sources).
  - **Hardware KVM switch:** one button or hotkey moves one monitor, keyboard and mouse between machines; no network and no software. It fits when both machines should use the same monitor. A monitor attached to the switch cannot also stay on another PC (comparison blogs).
  - **Remote desktop:** shows one machine's screen inside a window on the other. Sources frame it as for reaching a machine from elsewhere, not for switching at one desk.
- **Rule of thumb in the comparison blogs:** each machine with its own screen means software sharing; one shared screen means a hardware KVM; switching more than about five times a day favours a physical button (one vendor blog).
- **Mouse Without Borders details (Microsoft docs and Microsoft Q&A):** running PowerToys as administrator with "Use Service" lets it control elevated windows and the lock screen from the other computer, at higher security risk; file transfer has a 100 MB limit; clipboard and file sharing can be switched off; if the connection fails, the in-app firewall rule must be added on both devices. No latency figures were found.
- **Splitting the work for development (individual blogs):** a common pattern is to run the heavy workload on the desktop and use the laptop as the front end, through VS Code Remote SSH or VS Code Remote Tunnels. The host must stay on and awake; closing VS Code or the tunnel process ends the connection. One blog pairs this with tmux, SSH and Synergy, using the second computer as a "second monitor".
- **For agent sessions (inference, not a source):** because each machine's agents run locally on that machine, software sharing gives one keyboard and mouse across two screens while both machines keep running their own sessions. Remote Control (see `multi-device-agent-orchestration`) covers watching a session from the other machine's browser.

**Evidence strength:** vendor and comparison blogs plus Microsoft's PowerToys documentation (official for that tool's own behaviour); anecdotal for developer workflows. No head-to-head test, no latency or reliability data, and no survey of how common each route is.

**Sources:**

- [Mouse Without Borders](https://learn.microsoft.com/windows/powertoys/mouse-without-borders) (Microsoft docs; opened only through search snippets)
- [PowerToys running with administrator permissions](https://learn.microsoft.com/en-in/windows/powertoys/administrator) (Microsoft docs, search snippet)
- [Software KVM versus hardware KVM](https://us.ktcplay.com/blogs/product-comparisons/software-kvm-vs-hardware-kvm) (vendor blog)
- [Software or hardware KVM switch](https://www.avaccess.com/blogs/guides/kvm-switch-software-or-hardware/) (vendor blog)
- [KVM switch versus remote desktop](https://www.positioniseverything.net/kvm-switch-vs-remote-desktop-when-to-use-each/) (comparison blog)
- [Control two PCs with one keyboard and mouse](https://www.techradar.com/pro/the-clever-software-i-use-to-control-two-pcs-with-one-keyboard-and-mouse-no-hardware-kvm-required) (trade press)
- [Mouse and keyboard sharing apps](https://www.makeuseof.com/best-apps-sharing-mouse-and-keyboard-across-computers/) (trade press)
- [Second computer as a second monitor: tmux, SSH and Synergy](https://blog.devgenius.io/second-computer-as-a-second-monitor-web-development-with-tmux-ssh-and-synergy-d1186a273404) (individual blog)
- [SSH server setup for VS Code Remote](https://shunkei3.github.io/posts/ssh-server-setup/index.html) (individual blog)
- [VS Code tunnels as a remote coding server](https://www.positioniseverything.net/turn-your-desktop-into-a-remote-coding-server-with-vs-code-tunnels/) (comparison blog)

**Limits:** all pages were read as search-result summaries, none opened in full. Most sources are vendors selling the product they compare. Nothing found on ergonomics (one keyboard versus two), on Windows 11 specifics beyond Mouse Without Borders, on fatigue from watching two screens, or on switching tools that are not Windows-to-Windows.

**Checked:** 2026-11-23
