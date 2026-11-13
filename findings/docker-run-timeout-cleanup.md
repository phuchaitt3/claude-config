# Time-limiting a `docker run` without leaving the container behind

- **Question:** Does wrapping `docker run` in `timeout` (or a job runner's time limit) stop the container, and how do teams time-limit a container run so it is always cleaned up?
- **Checked:** 2026-11-13
- **Evidence strength:** *common practice* for the failure and the label or cidfile cleanup (several independent CI trackers and forum reports agree); *official standard* only for the flag definitions (Docker docs). No Docker document states what happens to the container when the client is killed.

## Finding

- **`docker run` is a client; the container belongs to the daemon.** Killing the client does not stop the container. A forum report reproduces it with `timeout -s SIGKILL 5 docker run --rm ubuntu sleep 30`: the container keeps running. With `--sig-proxy` (default true; Docker docs: "Proxy received signals to the process") a catchable signal such as SIGTERM sent to the client is forwarded to the container, but SIGKILL cannot be forwarded (community gist). A Red Hat bug on Podman, which uses the same model, says the container survives when `timeout -k` escalates to a kill, and recommends the runtime's own timeout over the `timeout` utility.
- **`--rm` does not help.** Docker docs: `--rm` removes the container "when it exits". A container that never exits is never removed, so `timeout ... docker run --rm` leaves an orphan (Keboola write-up: containers stopped by `timeout` "will not cleanup properly ... containers running with the remove flag will remain").
- **CI systems hit the same thing.** GitLab Runner, Jenkins (CERN, Osmocom), Bamboo and game-ci trackers all report containers left running after a job timeout or abort. Their fixes: a cleanup step that runs on its own deadline even after the job timed out (GitLab), a `trap` on TERM/EXIT that stops the containers and checks `docker ps` (Osmocom), stopping detached containers in a final task (Atlassian KB), a cidfile to know which container to stop (game-ci), and a sweep by a per-job label (`docker ps --filter label=...`, Capella CI template). A unique label per job keeps one run from stopping another's containers.
- **Docker's own deadline is for stopping, not for running.** `--stop-timeout` sets how long `docker stop` waits before a forced kill (default 10 s on Linux); there is no `docker run` flag that limits run time. So the pattern is: start named or labelled (`-d --name` or `--cidfile`), wait with your own deadline (`docker wait`, or poll), then `docker stop` / `docker rm -f` by name in a finally or trap step, with a label sweep as backstop. (Assembled from the sources above; no single source states the whole pattern.)
- **Windows makes it worse (checker's inference).** Git Bash's `timeout` and `taskkill /F` end `docker.exe` without a signal it can forward, so the SIGTERM path above does not apply; every timeout behaves like the SIGKILL case. Docker Desktop's containers run in the WSL 2 VM, which no client-side kill reaches. Seen on one laptop on 2026-11-13: `timeout 280 docker run --rm --gpus all ...` left the container running and holding GPU memory.

## Sources

- [Docker docs: `docker container run`](https://docs.docker.com/reference/cli/docker/container/run/) (official docs; `--sig-proxy`, `--rm`, `--stop-timeout`).
- [Docker Forums: killing a docker run process and its container](https://forums.docker.com/t/killing-a-docker-run-process-and-associated-container/80916) (forum).
- [Gist: SIGKILL to the docker client leaves the container running](https://gist.github.com/SkyperTHC/cb4ebb633890ac36ad86e80c6c7a9bb2) (community).
- [Red Hat Bugzilla 2090609: Podman and `timeout`](https://bugzilla.redhat.com/show_bug.cgi?id=2090609) (vendor bug tracker).
- [Keboola: timeout, but when?](https://500.keboola.com/timeout-but-when/) (engineering blog).
- [GitLab Runner issue 38725: container cleanup after job timeout](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/38725) and [GitLab issue 19906](https://gitlab.com/gitlab-org/gitlab/-/issues/19906) (vendor trackers).
- [Osmocom issue 3660: Jenkins containers left running](https://projects.osmocom.org/issues/3660) and [CERN LHCb: containers left running when Jenkins jobs are killed](https://gitlab.cern.ch/lhcb-core/nightlies-jenkins-scripts/-/issues/9) (project trackers).
- [Atlassian Bamboo KB: removing detached containers when the build stops](https://support.atlassian.com/bamboo/kb/how-to-make-sure-detached-containers-are-removed-once-the-build-stops/) (vendor KB).
- [game-ci PR 198: containers left by cancelled or timed-out workflows](https://github.com/game-ci/unity-test-runner/pull/198) and [Capella CI cleanup template](https://dsd-dbs.github.io/capella-dockerimages/ci-templates/gitlab/cleanup) (community projects).

## Limits

No official Docker statement covers the client-killed case; the behaviour rests on reproductions and trackers. The Windows point is inferred from how Git Bash and `taskkill` end processes plus one observed incident, not from a Docker source. Signal forwarding with a TTY (`-t`) was not checked.
