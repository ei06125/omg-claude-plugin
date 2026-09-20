# Containerization, Virtualization, and OCI Image Governance Standard

Last reviewed: 2026-09-20

This standard defines how the project selects, builds, runs, tests, publishes, and secures containers and virtual machines. It applies to developer workstations, CI, local integration environments, production workloads, and agent sandboxes. It complements the repository, CI/CD, identity, security, private-data, and quality governance guides in this directory.

It is a baseline, not a claim that every workload belongs in a container. Owners must document and approve departures where the workload, data classification, platform, or threat model needs stronger controls.

## 1. Normative language and goals

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

The goals are:

- deterministic, reviewable, reproducible builds;
- a small, understandable runtime attack surface;
- least privilege across host, VM, container, registry, network, and identity boundaries;
- immutable, traceable artifacts promoted between environments;
- clear separation between application packaging, runtime management, and isolation;
- a usable local development path on Linux, macOS, and supported CI runners.

## 2. Mental model: layers that are often confused

An OCI image, a container, a Linux container, a VM, a sandbox, and a Docker installation are related but are not interchangeable.

| Layer | Meaning | Boundary provided | Important limitation |
| --- | --- | --- | --- |
| OCI image | Content-addressed configuration plus filesystem layers | None by itself | An image is inert data, not a running workload. |
| OCI runtime bundle | Unpacked root filesystem plus `config.json` | None by itself | It is runtime input, not an image format. |
| Application container | Usually one application/process group from an image | Linux namespaces, cgroups, capabilities, LSM/seccomp policy | Shares the host kernel. |
| System container | A full Linux userspace sharing the host kernel | Same kernel-level controls, with a VM-like operational model | Is not a VM and cannot use a different kernel. |
| Virtual machine | Guest OS and guest kernel virtualized by a hypervisor | Hardware/virtualization boundary and separate kernel | Costs more resources and operational work. |
| Sandbox | A constrained execution environment; implementation varies | Depends on its implementation and policy | The name alone does not state the security boundary. |

### 2.1 OCI is the portability contract

OCI defines image, runtime, and distribution specifications. The image specification defines portable layered image content; the runtime specification defines how an unpacked bundle runs; and the distribution specification defines a registry API. Docker image references and registries commonly use these formats, but “Docker image” does not mean that Docker Engine is the only compatible builder or runtime.

Treat an image digest as the immutable artifact identity. A tag is a mutable convenience pointer and MUST NOT be the sole production deployment identity.

### 2.2 Containers are isolation, not a security guarantee

Linux containers use kernel features such as namespaces, cgroups, capabilities, seccomp, and—where available—SELinux or AppArmor. These controls reduce blast radius, but a kernel vulnerability, over-broad mount, privileged mode, host socket, device mapping, or weak runtime configuration can breach the intended boundary.

Containers are appropriate for ordinary application isolation when the host kernel is trusted and shared-kernel risk is acceptable. Use a VM or a purpose-built sandbox when a workload requires a different kernel, kernel module, broad device passthrough, stronger tenant separation, or execution of substantially untrusted code.

### 2.3 Rootless does not mean risk-free

Rootless containers reduce the consequences of container-runtime compromise by mapping container identities to unprivileged host identities. They SHOULD be preferred for developer and single-user use where compatible. They do not neutralize unsafe bind mounts, exposed credentials, vulnerable applications, outbound network access, or an intentionally granted privileged capability.

## 3. Architecture and responsibility boundaries

```text
source + lock files
        |
        v
builder (BuildKit / Nix / CI) --> OCI image manifest, config, layers, attestations
        |                                      |
        v                                      v
registry <---------------------- digest-pinned promotion and deployment
                                               |
                                               v
runtime manager (Docker Engine / containerd / Incus / Kubernetes)
                                               |
                                               v
OCI runtime (runc / crun) --> Linux kernel namespaces, cgroups, LSM, mounts

macOS / non-Linux host: CLI -> Linux VM (Lima/Colima/Docker Desktop) -> above stack
```

- **Build system:** turns source and declared inputs into an image. It MUST not embed secrets in an image or build cache.
- **Registry:** stores and serves OCI content. It MUST enforce authenticated push, authorization, immutable release references, retention, and auditability appropriate to the artifact classification.
- **Runtime manager:** retrieves images, assembles a root filesystem and OCI specification, configures lifecycle, storage and networking, and calls a runtime.
- **OCI runtime:** creates and starts the isolated process according to the OCI runtime specification. It is deliberately low level.
- **Host or guest kernel:** enforces the final kernel isolation. A container cannot be stronger than the operating system and configuration on which it runs.

## 4. Tool map and selection criteria

### 4.1 Docker

Docker is a product ecosystem, not merely a container format. Docker Engine provides the daemon, API, CLI and integrations; modern builds use BuildKit; Docker Desktop packages a developer experience and, on macOS and Windows, runs Linux containers inside a managed Linux VM.

Use Docker when repository tooling, Compose, a CI runner, or team workflow already requires the Docker CLI/API. Prefer BuildKit-enabled builds and `docker buildx` for modern builds, cache control, multi-platform output, and provenance/SBOM features.

The Docker daemon socket is a high-privilege control plane. Mounting it into a container normally lets code control the daemon and commonly the host. It MUST NOT be mounted into ordinary application or untrusted CI/agent workloads. Treat Docker daemon access as root-equivalent unless the platform’s documented rootless/authorization model demonstrably narrows it.

### 4.2 Lima

Lima launches Linux virtual machines with file sharing and port forwarding, with a focus on container development. It can run containerd/nerdctl, Docker, Kubernetes, Podman, or ordinary Linux applications. It is a VM layer, not an OCI runtime.

Use Lima directly when a team needs a configurable Linux VM and wants to choose the guest stack. On macOS, select the VM type and filesystem sharing deliberately: native virtualization support can be faster for matching architectures, while QEMU provides broader emulation compatibility. Do not assume that host paths, UID/GID behavior, inotify behavior, mount consistency, or network addresses equal native Linux behavior.

### 4.3 Colima

Colima is a higher-level tool built on Lima. It provisions a Linux VM and can provide Docker, containerd, Kubernetes, and Incus profiles. It is a pragmatic choice for local macOS/Linux development when Docker-compatible tooling is needed without using Docker Desktop.

Use named profiles to isolate projects or runtime configurations. Record the selected runtime, VM architecture, CPU, memory, disk, mount behavior, and Kubernetes setting in project onboarding documentation when they affect reproducibility. Avoid ambiguous shell state: confirm the active Docker context before building, testing, loading, pushing, or deleting images.

### 4.4 containerd and nerdctl

containerd is a daemon and API for managing image content, snapshots, containers, and tasks. It does not itself execute OCI processes: it prepares the root filesystem and runtime specification, then uses a shim and a lower-level runtime. Kubernetes commonly reaches containerd through its CRI plugin; `nerdctl` is a Docker-like CLI for containerd.

Use containerd directly for Kubernetes nodes, minimal OCI infrastructure, or when its namespaces, snapshotters, and CRI integration are explicitly desired. Do not assume Docker CLI state and containerd namespaces are interchangeable. In particular, images in one containerd namespace may not be visible to Kubernetes or another client namespace.

### 4.5 runc and crun

`runc` is a widely used OCI Runtime Specification implementation. `crun` is another OCI runtime implementation designed to be fast and lightweight. Both consume an OCI bundle and use Linux primitives to start the container process.

Application teams SHOULD select runtimes through the platform rather than invoking `runc` or `crun` directly. Direct use is suitable only for runtime development, controlled diagnostics, or a documented low-level platform use case. Pin and maintain the runtime as security-critical infrastructure; vulnerabilities here cross a central trust boundary.

Choose a runtime based on platform compatibility, cgroup/LSM needs, operational support, benchmarked behavior, and security maintenance—not a generic performance claim. Validate the exact runtime and version in the target environment.

### 4.6 Incus

Incus is a manager for system containers, OCI application containers, and virtual machines. System containers run a full Linux distribution using the host kernel through LXC; VMs use a separate kernel, implemented through QEMU. It provides a common API, projects, images, storage and networks across instance types.

Use Incus when full-system environments, a private-cloud-like interface, snapshots, multi-instance lifecycle management, or mixed system-container/VM workloads fit better than application-focused Docker/Compose. Use a VM for workloads needing a different kernel, kernel modules, or hardware passthrough that cannot be safely supported by a container.

Local Incus socket/API access is highly privileged: it can attach host filesystems and devices and alter isolation settings. Grant it only to people and automation trusted with host-root-equivalent authority. Privileged Incus containers MUST be an approved exception with documented compensating controls.

### 4.7 Docker Sandboxes (`sbx`)

`sbx` here means Docker Sandboxes, not unrelated commands that share the same name. It creates managed development/agent sandboxes, offers lifecycle and shell/exec operations, mounted workspaces, port publishing, secret handling, and network policy controls. Depending on platform and configuration, it can provide a VM-backed environment rather than only a same-kernel container boundary.

Use `sbx` for coding agents and risky development tasks when its workspace, secret, network and lifecycle policies are enabled and reviewed. Start from default-deny or the narrowest policy that permits necessary package registries, source control, artifact registries and AI endpoints. Do not select an “open” network policy by habit. Mount only the project and explicitly necessary paths; read-only mounts are preferred. Do not place credentials in the project just to make them visible to an agent.

`sbx` has local and cloud modes with differing behavior. CI and developer guides MUST state which is in use, where data resides, which ports are published, and which network destinations and credentials are permitted.

### 4.8 Nix for OCI images

Nix is a functional package manager and build system. Nixpkgs `dockerTools` can produce Docker-compatible/OCI-consumable image archives from declared derivations, without relying on a Docker daemon during the image build. This makes package closure, inputs, and image composition reviewable and can make image generation reproducible.

Prefer Nix image construction where the project already uses Nix, cross-environment reproducibility and dependency closure matter, or a daemonless CI build is valuable. `dockerTools.buildLayeredImage` is generally appropriate for registry/runtime layer sharing; `streamLayeredImage` can reduce local I/O for large images. Use `buildImage` only where its simpler single-layer approach is genuinely preferable.

Nix does not automatically guarantee a secure image. The final image still needs a non-root user, a minimal runtime closure, deterministic configuration, scanned dependencies, signed provenance, and correct runtime policy. Be aware that Nix store paths and dynamic loader behavior differ from conventional FHS-oriented images; test the result in the intended runtime.

## 5. Decision guide

| Need | Default choice | Escalate to |
| --- | --- | --- |
| One service or CI job; portable deployment | OCI application image | VM if shared kernel is unacceptable. |
| Local macOS Docker-compatible development | Colima profile or approved Docker Desktop setup | Lima for custom guest configuration. |
| Linux VM plus custom container engine | Lima | Incus for fleet/system-instance management. |
| Kubernetes node runtime | containerd through CRI | A platform-approved CRI runtime. |
| Full Linux distribution per instance | Incus system container | Incus VM if it needs its own kernel. |
| Kernel modules, different kernel, PCI/device passthrough | VM | Dedicated host where workload risk requires it. |
| Agent/untrusted-code execution | Docker Sandbox with restrictive policy or an approved VM sandbox | Isolated CI account/VM and reviewed egress controls. |
| Hermetic, declared image construction | Nix `dockerTools` | BuildKit/Dockerfile where ecosystem integration is the overriding need. |
| Low-level runtime work | runc/crun only in controlled platform work | Higher-level manager for ordinary workloads. |

## 6. Required image standards

### 6.1 Build inputs and reproducibility

- Images MUST be built from version-controlled definitions: Dockerfile/Containerfile, Nix expression/flake, or equivalent reviewed build definition.
- Build definitions MUST pin base-image digests or use an approved mechanism that resolves and records immutable inputs. `latest`, floating language-image tags, and mutable package indexes are not production inputs.
- Dependency lock files MUST be used where the ecosystem supports them and MUST be included in dependency-install cache keys.
- Builds MUST have a narrow build context. Maintain `.dockerignore` or the equivalent. Exclude `.git` when history is not required, credentials, local environments, test artifacts, caches, generated reports, and unrelated source.
- Build steps MUST be non-interactive and deterministic as practical. Time, random data, network fetches, and ambient host state SHOULD NOT affect production artifacts except through declared, recorded inputs.
- CI MUST build from a clean checkout and SHOULD verify that a rebuild yields the expected digest or reproducibility evidence where the toolchain supports it.
- Build caches are untrusted inputs. Do not allow a cache to bypass source, dependency, signature, policy, or vulnerability checks.

### 6.2 Dockerfile/Containerfile rules

- Use multi-stage builds so compilers, package managers, tests, source, and build-only credentials do not enter the runtime stage.
- Use a minimal, maintained runtime base or `scratch` only when the executable, certificates, timezone data, DNS behavior, and diagnostics needs are deliberately satisfied.
- Copy explicit artifacts from a named build stage. Do not copy an entire build workspace into the runtime stage.
- Prefer `COPY` to `ADD`; use `ADD` only when its special behavior is required and documented.
- Never use `curl | sh`, unverified remote installers, or unpinned downloads in a production image build. Verify source authenticity and integrity before execution.
- Combine package-index refresh and package installation in one cache-aware layer where using an OS package manager; remove package indexes/caches in the same layer when not needed at runtime.
- Do not run package-manager upgrade operations with uncontrolled versions in a release build.
- Do not use secrets in `ARG`, `ENV`, labels, command arguments, or copied files. Use BuildKit secret or SSH mounts for the shortest possible build step and confirm they do not persist in layers or logs.
- Set `USER` to a non-root numeric UID/GID in the final image unless root is technically required and explicitly approved.
- Define `WORKDIR`, `ENTRYPOINT`/`CMD`, exposed ports, volumes, and health checks only when they express the actual runtime contract. Do not use a shell-form command when exec-form avoids signal-handling and quoting ambiguity.

Example shape:

```Dockerfile
# syntax=docker/dockerfile:1
FROM example-registry/build-base@sha256:<pinned-digest> AS build
WORKDIR /src
COPY dependency-manifest dependency-lock ./
RUN <deterministic dependency installation>
COPY . .
RUN <build and test command>

FROM example-registry/runtime-base@sha256:<pinned-digest>
RUN <create fixed non-root user and writable directories>
USER 10001:10001
WORKDIR /app
COPY --from=build --chown=10001:10001 /src/dist/ ./
ENTRYPOINT ["/app/service"]
```

This is a pattern, not a copy-paste command. Substitute only reviewed registries, digests, build commands, and artifact paths.

### 6.3 Nix image requirements

- Pin the Nixpkgs revision through a lock file or an equivalent reviewed input. Do not use an unpinned channel for release images.
- Keep the image closure intentional. `copyToRoot`/`contents` includes store paths and their runtime dependencies; inspect its size and licenses rather than assuming it is minimal.
- Specify `config` explicitly: user, working directory, command/entrypoint, environment, labels, and exposed ports as needed.
- Keep default `created`/`mtime` values deterministic. Do not set them to the current time unless non-reproducibility is an approved requirement.
- Set ownership intentionally. A Nix-built image defaults to root ownership unless configured otherwise.
- Build per target platform or use an approved multi-platform build/publish process. Do not label an image multi-platform without testing every published manifest.
- Load/test the emitted archive in a compatible runtime before promotion. The archive is an artifact; it still needs registry scanning, signing and deployment-policy verification.

Illustrative expression:

```nix
{ dockerTools, myService }:
dockerTools.buildLayeredImage {
  name = "example-service";
  tag = "release";
  contents = [ myService ];
  config = {
    User = "10001:10001";
    WorkingDir = "/app";
    Entrypoint = [ "/bin/example-service" ];
  };
}
```

The actual package must create needed writable directories and must not assume a conventional distribution filesystem hierarchy.

### 6.4 Image metadata and artifact identity

- Release images MUST carry immutable source revision, build timestamp or reproducible-build indicator, builder identity, and OCI-standard labels where supported.
- CI MUST record source revision, build definition hash, base-image digests, dependency-lock identity, target platform, image digest, SBOM reference, vulnerability scan result, and attestation/signature reference.
- Use a release tag for human discovery and deploy the resolved digest. Configure registry immutability for release tags where available.
- Multi-platform image indexes MUST be tested on each supported architecture. Architecture emulation is useful for building/testing but does not replace native validation for performance- or kernel-sensitive workloads.

## 7. Required runtime security controls

### 7.1 Default runtime posture

- Run as a non-root user and drop unnecessary Linux capabilities. Add one capability only with a documented reason and test.
- Set `no-new-privileges` where the runtime supports it.
- Use a read-only root filesystem when the application can support it. Mount narrowly scoped writable volumes or temporary filesystems for required state.
- Define CPU, memory, process-count, storage, and timeout limits appropriate to the service. Capacity limits are availability and containment controls, not merely cost controls.
- Use a restrictive seccomp profile and platform LSM controls (AppArmor or SELinux) where available. Do not default to `unconfined`.
- Use user namespaces/rootless mode where compatible with the platform and workload.
- Avoid `--privileged`, host PID/IPC/network namespaces, arbitrary devices, `SYS_ADMIN`, `CAP_SYS_PTRACE`, writable host mounts, and Docker/containerd/Incus sockets. Each requires written approval, a limited scope, and a compensating-control plan.
- Do not bind privileged host ports or mount host paths merely for convenience. Prefer managed volumes and explicit port mappings.
- Keep production containers ephemeral. Put durable state in explicitly governed storage with backup, encryption, retention, and recovery controls.

### 7.2 Networking

- Start from no published ports and no inbound reachability beyond the workload’s defined contract.
- Segment services by network and allow only required east-west traffic. Do not rely on an “internal” network label as the only authorization control.
- Apply egress controls for sensitive, build, CI, agent, and untrusted workloads. Permit only documented domains/endpoints such as package registries, source control, artifact registries, identity providers, telemetry endpoints, and required APIs.
- Treat DNS as part of egress control. Logging only the destination IP is insufficient for policy and incident response.
- Terminate TLS and authenticate service-to-service access according to the project’s identity and security policy. Network location is not authorization.

### 7.3 Secrets and data

- Secrets MUST enter a running workload through the approved secret manager, workload identity, short-lived token, or runtime secret mechanism—not the image, source tree, image label, environment dump, or command line.
- Secret mounts SHOULD be read-only, scoped to one workload, and rotated. Do not log environment variables or process command lines in a way that exposes secrets.
- Developers MUST NOT copy host credential directories, cloud profiles, SSH agents, Docker configuration, or socket files into a container or sandbox by default.
- Classify mounted data. A writable source-tree mount gives the workload authority to alter that tree even when the workload is otherwise isolated.
- Backups, snapshots, image layers, build cache, and registry replication can contain sensitive data. They follow the same data-classification and retention controls as their source.

### 7.4 Agent sandbox requirements

Before executing an agent with broad shell or code-edit capability:

1. Choose a VM-backed sandbox or the strongest available isolation compatible with the task.
2. Mount only the project and only the necessary paths; prefer a disposable worktree for untrusted changes.
3. Set least-privilege network policy and observe connection logs.
4. Inject only task-scoped, revocable credentials through the sandbox’s secret facility.
5. Do not mount host container control sockets, private SSH keys, password stores, cloud credential directories, or unrelated repositories.
6. Set CPU, memory, disk, process, and wall-clock limits.
7. Publish only the required local ports and remove them after use.
8. Destroy disposable sandboxes after the task and retain only required audit records and artifacts.

## 8. Virtualization and host-platform rules

### 8.1 Linux hosts

Linux containers are closest to native on Linux because the kernel features are local. Still verify cgroup v2 configuration, user namespace policy, LSM state, storage driver/snapshotter, filesystem support, and rootless compatibility. Kernel and runtime patching are part of container security patching.

### 8.2 macOS hosts

Linux containers on macOS run in a Linux VM. Docker Desktop, Lima and Colima differ in VM management and integration, but the container process is not directly running against the macOS kernel.

- Treat the VM disk, shared folders, port forwards, active Docker context, and VM lifecycle as part of the local environment.
- Test Linux filesystem assumptions—case sensitivity, permissions, symlinks, file watching, socket behavior and performance—inside the guest.
- Match `arm64` images to Apple Silicon whenever possible. Use `amd64` emulation only when necessary, label it explicitly, and test it; emulation changes speed and can hide architecture-specific behavior.
- Never use a host-path mount to bridge around a guest permission or networking problem without reviewing the exposure.

### 8.3 VM policy

- Keep guest OS, hypervisor, firmware, and integration agents patched.
- Use separate VM profiles/projects for workloads with different trust levels.
- Disable nested virtualization and device passthrough unless required.
- Restrict VM management APIs, SSH access, image sources, host filesystem sharing, clipboard/port forwarding, and administrative groups.
- Snapshotting is not a backup policy. Validate restore, consistency, encryption, retention, and access control.

## 9. Runtime-specific operational guidance

### Docker and BuildKit

- Use `docker buildx build` or the approved CI builder for release images.
- Configure builders with explicit network and entitlement policy. `network.host`, `security.insecure`, and device access are privileged build capabilities and MUST NOT be enabled by default.
- Prefer remote cache only when access-controlled and attributable. Cache imports can expose metadata and consume untrusted content.
- Use multi-stage builds, build checks/linting, SBOM generation, provenance attestations, vulnerability scanning and signing where supported by the approved builder/registry pipeline.

### Colima and Lima

- Use profiles/instances rather than modifying a shared default VM without coordination.
- Check the current Docker context or `nerdctl` target before destructive image/container actions.
- Do not use VM defaults as a substitute for project requirements: record architecture, runtime, resource limits, mounts and port mappings.
- Stop unused VMs and remove obsolete images/volumes only under the project’s retention and data rules. Volumes may be irreplaceable state.

### containerd

- Configure the correct runtime and cgroup driver for the platform. For Kubernetes, kubelet and runtime cgroup policy MUST align.
- Understand containerd namespaces. Audit commands and clean-up actions MUST state the namespace they affect.
- Use the CRI interface for Kubernetes lifecycle management; do not mutate Kubernetes-managed containers through unrelated low-level tooling except under an incident procedure.
- Protect the containerd socket as privileged host infrastructure.

### Incus

- Use Incus projects, profiles, storage pools, networks and remote certificates to establish isolation and ownership boundaries.
- Prefer unprivileged containers. Enable nesting, syscall interception, raw device access, idmap exceptions, and privileged mode only when documented and approved.
- For VMs, manage guest patching, images, UEFI/Secure Boot choices, and agent access independently of the Incus host.
- Treat a local Unix socket membership and remote API trust certificate as powerful administrative access. Review regularly.

### runc and crun

- Do not expose runtime binaries or their state directories to application users.
- Maintain OCI runtime and shim versions with the host’s security patch process.
- Debug bundles, runtime logs and process state can expose mounts, environment, paths and identifiers; protect them accordingly.
- Use runtime choice only through an approved containerd/Docker/CRI configuration for normal workloads.

### Podman

Podman is a daemonless, Linux-native OCI container and image tool. It can run as root or as an unprivileged user, uses OCI runtimes such as `crun` or `runc`, supports pods, and can expose a Docker-compatible API for tools that need it. A Podman container is not inherently safer merely because Podman has no always-running daemon; isolation still depends on user namespaces, mounts, capabilities, network, seccomp/LSM policy, the kernel, and the selected runtime.

- Prefer rootless Podman for developer and CI workflows where its networking, storage and image-build behavior meets requirements. Verify subuid/subgid mappings, user namespaces, storage, volume ownership, port forwarding and egress behavior on the target host.
- Use `podman generate systemd` or Quadlet/systemd integration only where lifecycle ownership, restart behavior, logging, ordering and upgrade/rollback behavior are defined. Do not use an interactive developer command as an undocumented production supervisor.
- Pods share namespaces according to their configuration. Put only tightly coupled containers—such as an application and a deliberate sidecar—in one pod. Pod membership is not a substitute for authentication, authorization, network policy, or resource limits.
- Rootful Podman and the Podman API socket are privileged infrastructure. Protect socket access and do not mount it into untrusted containers, CI jobs or agents.
- `podman compose` is a compatibility wrapper, not an independent orchestration security model. Apply the same image, secret, mount, network, user, capability and resource rules as Docker Compose.

### Kubernetes

Kubernetes is an extensible declarative control plane for containerized workloads. A cluster has a control plane and worker nodes. The control plane exposes and stores desired state, schedules Pods and reconciles resources; each node runs a kubelet, a CRI-compatible container runtime and network support. Kubernetes manages Pods—not individual containers—as its smallest deployable unit. A Pod may contain one or more tightly coupled containers sharing network and storage.

Use Kubernetes when declarative desired state, scheduling, self-healing, service discovery, controlled rollouts, autoscaling, multi-node placement, and a governed platform are necessary. Do not adopt it merely to run a small, single-host service: operational ownership of the API, identities, node OS/runtime, CNI, CSI/storage, ingress, observability, upgrades, backup and incident response is substantial.

#### Kubernetes workload design

- Use Deployments for stateless replicated applications; StatefulSets only where stable identity and ordered storage/lifecycle semantics are necessary; Jobs/CronJobs for bounded work; and DaemonSets only for a justified per-node service.
- Keep one primary application per Pod by default. Sidecars require a defined lifecycle, resource budget, network contract, failure behavior and security context.
- Declare readiness, liveness and startup probes that measure the actual service contract. A probe MUST NOT require a broad administrative credential or mutate production state.
- Set CPU and memory requests and limits for every container, not only the Pod. Requests guide scheduling; limits constrain runtime consumption. Evaluate CPU limits carefully for latency-sensitive workloads because throttling can degrade service even when a node has spare CPU.
- Use namespaces as administrative, policy and tenancy boundaries. Each namespace MUST have an owner, intended data classification, RBAC model, ResourceQuota, LimitRange, default network policy and lifecycle/retention policy.
- Use persistent volumes only for explicitly stateful data. Define storage class, encryption, access mode, backup, restore test, retention, migration and deletion/reclaim policy. `emptyDir` and container filesystems are ephemeral and MUST NOT be treated as durable storage.
- Pin every production container image by digest. Kubernetes image tags can change in a registry; digest references ensure the same image is started. Image pull policy does not make a mutable tag immutable.

#### Kubernetes security and policy

- Restrict Kubernetes API, kubelet, etcd and control-plane administrative endpoints. Use TLS, authenticate every client, authorize with least-privilege RBAC, and audit sensitive API operations. Never expose etcd or kubelet APIs publicly.
- Enforce the Pod Security Standards `restricted` profile for application namespaces unless an approved exception needs a less restrictive profile. Use Pod Security Admission and/or a validating admission policy/webhook to block prohibited configurations.
- Admission policy MUST reject or explicitly approve: privileged Pods; host PID/IPC/network; hostPath volumes; dangerous capabilities; `allowPrivilegeEscalation`; root execution; absent seccomp; untrusted registries; floating tags; missing resource constraints; and policy-bypassing ServiceAccounts.
- Default-deny ingress and egress with NetworkPolicy, then allow only required traffic. Confirm that the selected CNI actually enforces NetworkPolicy; a NetworkPolicy object has no effect with a plugin that does not implement it. Consider DNS, cloud metadata endpoints, node traffic and service-mesh behavior in the policy design.
- Use distinct ServiceAccounts per workload where API access is necessary. Disable automatic service-account token mounting for workloads that do not need Kubernetes API access. Do not use the `default` ServiceAccount as an application identity.
- Kubernetes Secrets provide an API mechanism, not sufficient secret governance by themselves. Enable encryption at rest where applicable, restrict `get`, `list` and `watch` access, use external/workload-identity secret systems for high-value credentials, and prevent secret values from appearing in manifests, images, logs or CI output.
- Use admission controls and policy-as-code to verify allowed registries, image signatures/provenance, SBOM/vulnerability policy, digest pinning and required runtime security context before persistence. Admission policy is defense in depth; it does not replace review or runtime monitoring.
- For stronger workload isolation, select a RuntimeClass backed by an approved runtime or sandboxed runtime. Document its node compatibility, performance, feature limitations and operational support.

#### Kubernetes operations and release controls

- Manage cluster and workload manifests declaratively in version control. Use a reviewed reconciler or CI/CD identity with narrowly scoped namespace permissions; do not rely on a developer's personal `kubectl` credentials for production changes.
- Separate cluster administration from application deployment. Application teams MUST NOT receive cluster-admin, node proxy, secret-read-all, or arbitrary workload-creation privileges unless an approved role requires it.
- Use rolling updates with explicit readiness, availability, surge/unavailability, progress-deadline and rollback behavior. Record the deployed image digest and manifest revision.
- Restrict `LoadBalancer`, `NodePort`, external IP, ingress and egress-gateway creation. An externally reachable service requires an owner, authentication/authorization, TLS, network policy, logging, rate limiting and incident contact.
- Back up and restore-test cluster state and persistent data. An etcd backup is sensitive control-plane data and MUST be encrypted, access-controlled and tested separately from application-volume recovery.
- Patch and rotate the node OS, Kubernetes components, container runtime, CNI/CSI, admission controls, registry credentials and cluster certificates on a documented cadence. Drain/upgrade nodes with workload disruption budgets and rollback plans.
- Collect and protect audit logs, control-plane logs, node/runtime logs, workload logs, metrics and traces. Do not centralize secrets or sensitive payloads in logs.

### Minikube

Minikube is a local Kubernetes implementation for learning and development. It can run Kubernetes through a container driver or a VM driver; the driver determines the actual host/guest, networking, filesystem and privilege boundary. It is valuable for reproducing Kubernetes manifests and basic platform behavior locally, but it is not a production-cluster substitute.

- Use a named Minikube profile per project or experiment. Record the profile name, Kubernetes version, driver, architecture, node count, container runtime, CPU, memory, disk, enabled add-ons, network and published/tunneled services in developer documentation or automation.
- Select the driver deliberately. On Linux, a container driver can share the host kernel and its security characteristics; VM drivers provide a guest-kernel boundary. On macOS, Docker/Podman drivers still depend on their Linux VM. Do not compare Minikube driver modes as if their isolation or filesystem behavior were identical.
- Prefer a VM or isolated container runtime for risky experimentation. Do not point a Minikube profile at production credentials, registries with write authority, cloud control planes, secrets, host Docker/containerd/Podman sockets, or broad host mounts.
- Treat `minikube mount`, host access, ingress, `service`, `tunnel`, dashboard and add-ons as explicit exposure decisions. Bind and publish only needed development ports, do not make the dashboard publicly reachable, and remove tunnels/mounts after use.
- Apply the same Kubernetes baseline locally: namespace ownership, non-root workloads, resource requests/limits, digest-pinned images, Pod Security Admission, NetworkPolicy where the driver/CNI enforces it, scoped ServiceAccounts and externalized secrets. A local cluster is not exempt from secure manifest design.
- Avoid the `none`/bare-metal driver except for an approved advanced integration scenario. It alters host Kubernetes and runtime paths, has a mixed root/non-root model, can interfere with other software, and is inappropriate for an ordinary developer workstation.
- Use Minikube for local validation; test release manifests against the supported production Kubernetes version, CRI runtime, CNI, storage class, ingress implementation, admission policies and cloud integrations before promotion.

## 10. CI/CD, registry, release, and admission requirements

- CI runners that build images MUST be isolated from untrusted pull-request code to a level matching their credentials and deployment authority.
- Prefer rootless or remote builders with narrowly scoped credentials. Docker-in-Docker, a shared host Docker socket, and privileged build pods are exceptions requiring a threat-model review.
- CI MUST authenticate to registries with scoped, short-lived credentials when possible. Pull and push permissions MUST be separated where practical.
- Only CI/release automation may push protected release tags or promote release artifacts.
- Release promotion MUST copy or reference the already-built digest; it MUST NOT rebuild identical-looking source in each environment.
- Generate an SBOM and scan the final image. Scan build stages or build context as well when their dependencies matter to policy, provenance, or incident response.
- Define vulnerability severity thresholds, exception owner, expiry, remediation date, and compensating controls. A scan without a triage process is not an effective control.
- Sign artifacts and attach provenance/attestations where the registry and deployment platform support it. Deployment policy SHOULD verify the expected issuer, repository, source revision and digest.
- Keep registry retention policies that preserve deployed and rollback artifacts while expiring superseded development images and caches safely.
- Maintain an incident procedure to identify every deployment of an image digest, revoke a compromised image, block further pulls, rotate affected credentials, rebuild from corrected inputs, and deploy a replacement.

## 11. Testing and verification

Every production-bound image MUST have proportional evidence for:

- successful build from a clean CI checkout;
- unit/integration tests relevant to the artifact;
- startup, readiness and graceful shutdown behavior;
- non-root execution and required writable-path behavior;
- intended exposed port, TLS/authentication, and network-policy behavior;
- architecture-specific execution for every published platform;
- image digest, base-image digest, SBOM, vulnerability scan and signature/provenance records;
- container configuration inspection: user, capabilities, mounts, network, read-only root filesystem, resource limits and secret sources;
- rollback or replacement procedure for a deployed digest.

For system containers and VMs additionally test boot, guest patching, network isolation, storage recovery, console/agent access, backups and restore.

## 12. Exceptions

An exception request MUST state:

- workload and owner;
- precise control to be bypassed (for example, privileged mode, host networking, Docker socket, root user, unpinned base, or unrestricted egress);
- technical necessity and alternatives considered;
- affected host, environment, data classification and trust boundary;
- scope, duration and expiry;
- compensating controls, monitoring and rollback/removal plan;
- security/platform approval appropriate to risk.

Exceptions expire. They MUST be removed, renewed, or escalated before expiry; they MUST NOT become implicit permanent configuration.

## 13. Review checklist

Before approving an image, runtime, VM, sandbox, or platform change, verify:

- [ ] The selected abstraction matches the trust boundary: container, system container, VM, or sandbox.
- [ ] Source, dependencies, base images and Nix inputs are immutable and recorded.
- [ ] The final image excludes source, build tools, secrets and unnecessary packages.
- [ ] Runtime user is non-root or the root exception is documented.
- [ ] Capabilities, seccomp/LSM, namespaces, read-only filesystem, resource limits, mounts and network policy are intentional.
- [ ] No privileged socket, device, broad host mount, `--privileged`, host network, or unrestricted egress exists without an approved exception.
- [ ] Secrets use approved injection and do not appear in layers, logs, metadata or command lines.
- [ ] Tags are convenience references; deployment records and manifests use a digest.
- [ ] SBOM, scan, provenance/signature, target architecture and test evidence exist.
- [ ] Registry and runtime administrative access follow least privilege and are auditable.
- [ ] Stateful volumes, snapshots and VM disks have defined ownership, backup, retention and recovery behavior.
- [ ] Podman rootless/rootful mode, API socket exposure, pods and systemd lifecycle are intentional.
- [ ] Kubernetes namespace ownership, RBAC, Pod Security Admission, resource policy, NetworkPolicy enforcement, ServiceAccount and secret access are verified.
- [ ] Kubernetes production image references resolve to approved immutable digests and workload/cluster manifests have tested rollout and rollback behavior.
- [ ] Minikube profile, driver, host mounts, network/tunnel exposure, add-ons and local credentials are intentional and isolated from production authority.

## 14. Authoritative references

- [Open Container Initiative specifications](https://opencontainers.org/) — OCI image, runtime and distribution contracts.
- [OCI specification releases](https://specs.opencontainers.org/) — current published specification versions.
- [Docker build best practices](https://docs.docker.com/build/building/best-practices/) — multi-stage and image-construction guidance.
- [Docker Build documentation](https://docs.docker.com/build/) — BuildKit and build capabilities.
- [Docker Sandboxes usage](https://docs.docker.com/ai/sandboxes/usage/) and [`sbx exec` reference](https://docs.docker.com/reference/cli/sbx/exec/) — sandbox operating model and CLI behavior.
- [Lima](https://github.com/lima-vm/lima) — Linux VM environment and supported container-engine patterns.
- [Colima](https://github.com/abiosoft/colima) and [Colima FAQ](https://github.com/abiosoft/colima/blob/main/docs/FAQ.md) — Lima-based runtime profiles and Docker contexts.
- [Incus instances](https://linuxcontainers.org/incus/docs/main/explanation/instances/) and [Incus security](https://linuxcontainers.org/incus/docs/main/) — system/application containers, VMs and administrative-risk model.
- [containerd Runtime v2 architecture](https://github.com/containerd/containerd/blob/main/docs/runtime-v2.md) and [content flow](https://github.com/containerd/containerd/blob/main/docs/content-flow.md) — manager, shim, runtime and snapshot lifecycle.
- [`runc` manual](https://github.com/opencontainers/runc/blob/main/man/runc.8.md) and [`crun` manual](https://github.com/containers/crun/blob/main/crun.1.md) — OCI runtime behavior.
- [Kubernetes container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/) — CRI and cgroup-driver requirements.
- [Kubernetes cluster architecture](https://kubernetes.io/docs/concepts/architecture/) and [Pods](https://kubernetes.io/docs/concepts/workloads/pods/) — control plane, nodes and workload boundaries.
- [Kubernetes security](https://kubernetes.io/docs/concepts/security/), [security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) and [policies](https://kubernetes.io/docs/concepts/policy/) — security controls, policy and admission baseline.
- [Kubernetes NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) and [container images](https://kubernetes.io/docs/concepts/containers/images/) — enforceable network controls and digest-pinned images.
- [Podman documentation](https://docs.podman.io/) — daemonless OCI runtime, rootless operation, pods and system integration.
- [Minikube start guide](https://minikube.sigs.k8s.io/docs/start/) and [driver reference](https://minikube.sigs.k8s.io/docs/drivers/) — local development scope and container/VM/bare-metal driver behavior.
- [Nixpkgs `dockerTools` documentation](https://github.com/NixOS/nixpkgs/blob/master/doc/build-helpers/images/dockertools.section.md) — layered and streamed Docker-compatible image generation.
