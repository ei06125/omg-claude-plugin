# Software Quality and Testing Governance Guide

Last reviewed: 2026-09-19

This guide provides a practical baseline for software verification, validation, testing, BDD, TDD, performance engineering, fuzzing, security testing, and penetration testing. Organisational quality governance is defined separately in [quality-management-system-governance.md](quality-management-system-governance.md). Adapt this guide to product risk, architecture, release frequency, legal obligations, and customer commitments.

## 1. Relationship to the Quality Management System

The Quality Management System (QMS) defines company-wide quality policy, objectives, processes, responsibilities, document control, supplier governance, audits, management review, nonconformity handling, corrective action, and continual improvement. This software testing guide is one operational control within that system.

Software quality evidence should feed the QMS through objectives, risk registers, customer feedback, nonconformities, corrective actions, audits, and management reviews. QMS decisions should, in turn, define required assurance, independence, records, and improvement work for software delivery.

Testing provides evidence and reduces uncertainty. It cannot prove that non-trivial software has no defects.

## 2. Testing and debugging

Testing is a set of static and dynamic activities used to evaluate a test object, expose defects and risks, and provide decision evidence. It is one form of quality control and also supplies feedback for quality assurance and continual improvement.

Static testing examines artifacts without executing the software: requirements review, design review, code review, linting, type checking, static security analysis, and formal analysis. Dynamic testing executes software and observes behaviour.

Debugging locates, analyses, and removes the cause of a failure. Testing reveals a failure or risk; debugging explains and corrects it. After a correction, run confirmation tests and appropriate regression tests.

## 3. Verification and validation

### Verification: “Did we build the product correctly?”

Verification checks whether work products satisfy specified requirements, designs, contracts, and standards.

Examples:

- Reviewing requirements for consistency and testability.
- Checking an API against its schema.
- Testing a calculation against its specification.
- Confirming that code follows an approved design and coding standard.

### Validation: “Did we build the correct product?”

Validation checks whether the completed or evolving product satisfies user needs and intended use in realistic conditions.

Examples:

- Usability studies with representative users.
- Acceptance tests derived from business outcomes.
- Field trials, beta releases, and operational exercises.
- Confirming that a technically correct feature solves the actual problem.

A product can pass verification and fail validation: it may implement the written requirement perfectly while the requirement itself is wrong or incomplete. Perform both throughout development rather than leaving validation until final acceptance.

## 4. Define a quality model

Use a quality model to avoid treating functional correctness as the only concern. ISO/IEC 25010:2023 defines a product quality model with nine characteristics and supporting subcharacteristics. Use it to select requirements, design objectives, acceptance criteria, measures, and tests appropriate to the product.

Common concerns include:

- Functional suitability and correctness.
- Performance efficiency and capacity.
- Compatibility and interoperability.
- Interaction capability, accessibility, and usability.
- Reliability, availability, fault tolerance, and recoverability.
- Security and resistance to misuse.
- Maintainability, modularity, analysability, modifiability, and testability.
- Flexibility and adaptability.
- Safety where software can cause physical, financial, social, or environmental harm.

Do not require every product to maximise every characteristic. Record priorities and trade-offs. A medical device, internal report, payment API, and marketing site have different quality risks.

Source: [ISO — ISO/IEC 25010:2023 product quality model](https://committee.iso.org/standard/78176.html)

## 5. Software test planning and governance

Each product or material initiative should define:

- Scope, intended users, critical journeys, and unacceptable outcomes.
- Functional and quality requirements.
- Regulatory, contractual, security, privacy, accessibility, and operational obligations.
- Risk classification and failure impact.
- Test levels and test types required.
- Environments, data, tools, and responsibilities.
- Entry, suspension, resumption, and exit criteria.
- Defect severity, priority, ownership, and release policy.
- Evidence and retention requirements.
- Independence needed for review or testing.
- Production verification, monitoring, and rollback criteria.

Maintain traceability between significant requirements or risks and their design, implementation, tests, results, defects, exceptions, and release decision. Apply more formality to higher-risk functionality.

## 6. Risk-based testing

Prioritise testing by the likelihood of failure and potential impact. Consider:

- Safety, financial, privacy, security, legal, and reputational harm.
- Number and vulnerability of affected users.
- Change size, novelty, complexity, and dependency risk.
- Defect history and code churn.
- Recoverability, detectability, and blast radius.
- Availability of compensating controls or gradual rollout.

For each material risk, identify preventive controls, detection methods, test coverage, expected evidence, owner, and residual risk. Do not spend equal effort on every path while leaving critical failure modes lightly tested.

## 7. Test levels

### Unit or component testing

Tests small units of behaviour in isolation or with narrow dependencies. It should be fast, deterministic, readable, and run continuously.

Good unit tests:

- Focus on public behaviour and important invariants.
- Cover normal, boundary, error, and state-transition cases.
- Avoid excessive mocking of internal implementation.
- Produce a clear failure that identifies the broken behaviour.
- Run without network, clock, randomness, or filesystem instability unless those are deliberately controlled.

### Component or service testing

Tests a deployable component or service through its meaningful interface with controlled dependencies. It can verify routing, serialisation, persistence behaviour, errors, authentication, authorisation, and observability more realistically than a unit test.

### Integration testing

Tests interactions between components, databases, queues, external services, identity providers, and infrastructure. Validate contracts, timeouts, retries, idempotency, ordering, partial failure, version skew, and recovery.

Use realistic implementations where integration risk matters. A mock can confirm that code made the expected call but cannot prove compatibility with the real dependency.

### System and end-to-end testing

Tests the integrated system against important user and operational journeys. Keep this suite selective: end-to-end tests are valuable but slower, more fragile, harder to diagnose, and expensive to maintain.

### Acceptance testing

Confirms that the product meets agreed business and user acceptance criteria. Acceptance is a decision based on evidence and residual risk, not merely a separate test suite.

### Operational acceptance testing

Validates deployability and operability: installation, configuration, migration, monitoring, alerts, backup, restoration, capacity, failover, rollback, support procedures, and incident response.

## 8. Test portfolio and test architecture

Use many fast, focused checks and fewer broad, expensive checks. The exact shape may resemble a test pyramid, test trophy, or another model, but the objective is rapid feedback plus realistic confidence.

A balanced portfolio can include:

- Static checks and reviews.
- Unit/component tests.
- Contract and integration tests.
- Focused end-to-end journeys.
- Exploratory and usability testing.
- Performance, resilience, security, accessibility, and recovery tests.
- Production monitoring and controlled experiments.

Do not duplicate identical assertions at every level. Put a behaviour at the lowest level that can test it reliably, then use higher levels for integration risks and critical journeys.

## 9. Test design techniques

Apply techniques deliberately rather than inventing only happy-path examples:

- **Equivalence partitioning:** select representatives from classes expected to behave alike.
- **Boundary-value analysis:** test values at, below, and above limits.
- **Decision tables:** cover combinations of business conditions and outcomes.
- **State-transition testing:** cover valid, invalid, and recovery transitions.
- **Pairwise/combinatorial testing:** cover important parameter interactions without enumerating every combination.
- **Use-case and scenario testing:** exercise user and system workflows.
- **Error guessing:** target likely failures using domain knowledge and defect history.
- **Property-based testing:** generate inputs and check general invariants rather than only fixed examples.
- **Metamorphic testing:** verify relationships between outputs when an exact oracle is difficult.
- **Model-based testing:** derive tests from a behavioural or state model.
- **Mutation testing:** deliberately alter code to assess whether tests detect meaningful faults.

Document the oracle: the source of expected results. An assertion is only as trustworthy as the expectation behind it.

## 10. Test-Driven Development

TDD is a development practice that uses a short red–green–refactor cycle:

1. **Red:** write a small test expressing the next behaviour and confirm it fails for the expected reason.
2. **Green:** implement the simplest appropriate change that makes the test pass.
3. **Refactor:** improve design while keeping the suite green.

Benefits can include executable design feedback, small increments, regression protection, and testable interfaces. TDD is not synonymous with unit testing and does not replace integration, system, security, usability, or acceptance testing.

Practices:

- Start from observable behaviour, not private methods.
- Add one meaningful behaviour at a time.
- Confirm a new test fails before implementation so a false-positive test is not mistaken for protection.
- Refactor test code as production code.
- Avoid mocks that reproduce the implementation and make refactoring unnecessarily expensive.
- Use characterization tests before modifying poorly understood legacy behaviour.

TDD may not be the best first tool for disposable prototypes, visual exploration, or investigation where the problem is not yet understood. Once behaviour stabilises, capture important rules and regressions.

## 11. Behaviour-Driven Development and Gherkin

BDD is a collaborative discovery and development practice. Its purpose is shared understanding of valuable behaviour through concrete examples; using Cucumber or writing Gherkin alone does not establish BDD.

A useful rhythm is:

1. **Discovery:** product, development, and testing perspectives explore rules, examples, questions, and edge cases.
2. **Formulation:** express selected examples clearly in domain language.
3. **Automation:** connect stable, valuable examples to executable checks and implement the behaviour.

Source: [Cucumber — Behaviour-Driven Development](https://cucumber.io/docs/bdd/)

### Gherkin structure

```gherkin
Feature: Account lockout
  Registered users must be protected from repeated password guessing.

  Rule: Repeated invalid passwords temporarily lock the account

    Scenario: Account is locked after the permitted failures
      Given Alice has an active account
      And Alice has entered an invalid password four times
      When Alice enters an invalid password again
      Then Alice's account is temporarily locked
      And Alice is informed how to recover access
```

- `Feature` describes a capability.
- `Rule` groups examples of one business rule.
- `Scenario` or `Example` illustrates one concrete behaviour.
- `Given` establishes relevant context.
- `When` describes the event or action.
- `Then` states observable outcomes.
- `And` and `But` improve readability.
- `Scenario Outline` with `Examples` expresses the same rule over a meaningful data table.

Source: [Cucumber — Gherkin reference](https://cucumber.io/docs/gherkin/reference/)

### Gherkin guidelines

- Describe behaviour and business intent, not clicks, selectors, API calls, or implementation.
- Use the domain’s language consistently.
- Keep scenarios independent, focused, declarative, and brief.
- Cover one rule per scenario and include meaningful negative and boundary examples.
- Avoid large `Background` sections that hide essential context.
- Avoid using Gherkin for every low-level unit case; it creates expensive prose without improving shared understanding.
- Review feature files as product documentation and delete obsolete or duplicate scenarios.
- Keep step definitions cohesive. Prevent multiple phrases from expressing the same concept.

Source: [Cucumber — Writing better Gherkin](https://cucumber.io/docs/bdd/better-gherkin/)

## 12. Exploratory and manual testing

Automation checks known expectations efficiently. Exploratory testing simultaneously learns, designs, and executes tests to discover risks that scripted checks may miss.

Use time-boxed charters that state mission, scope, risks, data, and environment. Record observations, coverage, questions, defects, and follow-up. Useful targets include new functionality, complex workflows, error recovery, unusual sequences, confusing interfaces, accessibility, and areas with weak specifications.

Manual testing remains valuable when judgment, perception, learning, or human interaction matters. Avoid repetitive manual regression that can be automated reliably.

## 13. Functional testing

For every important capability, cover:

- Happy path and alternate valid paths.
- Invalid, missing, malformed, duplicate, stale, and unauthorised input.
- Minimum, maximum, empty, zero, negative, Unicode, locale, and time-zone boundaries as relevant.
- State transitions, retries, cancellation, interruption, and recovery.
- Idempotency and duplicate delivery.
- Concurrency, ordering, race conditions, and lost updates.
- Partial dependency failure and timeout.
- Compatibility with supported clients and versions.
- Audit, notification, and observability outcomes.
- Cross-tenant and object-level isolation.

Test failure behaviour as deliberately as success behaviour.

## 14. Contract and compatibility testing

Use schema and consumer/provider contract tests for APIs, events, files, and integrations. Confirm:

- Required and optional fields.
- Type, format, constraints, and semantics.
- Backward and forward compatibility.
- Unknown-field handling.
- Error structures and status codes.
- Authentication and authorisation expectations.
- Idempotency, ordering, pagination, and rate limits.
- Version negotiation and deprecation.

Contract tests reduce—but do not eliminate—the need for integration tests against real infrastructure and third parties.

## 15. Performance and capacity testing

Performance testing should answer a defined question with production-relevant workloads and service objectives.

### Test types

- **Load testing:** expected normal and peak demand.
- **Stress testing:** operation beyond intended capacity to find limits and failure modes.
- **Spike testing:** abrupt changes in demand.
- **Soak or endurance testing:** sustained load to reveal leaks, exhaustion, and degradation.
- **Volume testing:** large datasets, queues, files, indexes, or histories.
- **Scalability testing:** relationship between resources, load, and throughput.
- **Concurrency testing:** contention, races, locks, and simultaneous operations.
- **Baseline and regression testing:** detect meaningful performance change between versions.

### Design requirements

- Define latency percentiles, throughput, error rate, saturation, resource limits, and recovery criteria before running the test.
- Model user journeys, request mix, data size, think time, cache state, geographic latency, background jobs, and dependency behaviour.
- Use percentiles such as p95 and p99 rather than averages alone.
- Observe application, database, queue, runtime, host, network, and dependency metrics.
- Warm up where appropriate and separate steady-state results from startup effects.
- Control the load generator so it does not become the bottleneck.
- Repeat under comparable conditions and record code, configuration, infrastructure, dataset, and tool versions.
- Test graceful degradation, overload protection, queue growth, backpressure, and recovery after load falls.

Never run disruptive tests against production without explicit authorisation, safeguards, monitoring, stop conditions, and incident coordination.

## 16. Resilience, recovery, and reliability testing

- Inject dependency latency, errors, disconnects, and malformed responses.
- Terminate instances and verify restart, rescheduling, and in-flight request behaviour.
- Exercise zone, region, network, database, queue, and identity-provider failure where relevant.
- Validate retry limits, exponential backoff, jitter, circuit breakers, bulkheads, and idempotency.
- Fill disks, exhaust pools, expire certificates, rotate keys, and test clock skew in controlled environments.
- Restore backups and verify data integrity, not only job success.
- Measure recovery time and recovery point against objectives.
- Test rollback and roll-forward with database and message-schema changes.

Chaos engineering is a disciplined experiment on system resilience, not unplanned breakage. State the hypothesis, blast radius, observability, abort conditions, and recovery plan.

## 17. Fuzz testing

Fuzzing generates or mutates inputs to discover crashes, hangs, excessive resource use, assertion failures, memory errors, parser inconsistencies, and security weaknesses.

Apply fuzzing to parsers, protocol handlers, file formats, serialisers, codecs, compilers, query languages, authentication inputs, and other broad input surfaces.

### Fuzzing approaches

- **Mutation-based:** changes existing valid or seed inputs.
- **Generation-based:** creates inputs from a grammar, schema, or model.
- **Coverage-guided:** uses execution feedback to explore new paths.
- **Structure-aware:** preserves enough input structure to reach deeper logic.
- **Differential:** compares multiple implementations or modes for inconsistent results.
- **Stateful/protocol fuzzing:** explores sequences and state transitions, not only individual messages.

### Fuzzing practice

- Build a small, deterministic harness around the target.
- Seed with valid, invalid, boundary, and previously failing cases.
- Use sanitizers and runtime checks to expose memory and undefined-behaviour defects.
- Set resource limits and detect hangs, leaks, and uncontrolled output.
- Minimise crashing inputs and store them as regression tests.
- Deduplicate findings by root cause.
- Track coverage and corpus growth, but judge success by risk reduction and fixed defects.
- Run continuously for important attack surfaces; longer execution often reaches deeper states.
- Do not expose real secrets or production data in corpora.

Fuzzing complements example-based and property-based testing. It does not establish functional correctness by itself.

## 18. Security testing

Integrate security checks throughout the lifecycle. NIST’s Secure Software Development Framework recommends defining security-check criteria and integrating secure practices into the SDLC.

Source: [NIST SP 800-218 — Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final)

### Static Application Security Testing

SAST analyses source or compiled code for potentially unsafe patterns. Tune rules to the languages and threat model, triage findings, and track false positives. SAST does not understand every business rule and cannot replace review or dynamic testing.

### Dynamic Application Security Testing

DAST probes a running application from the outside. It can find runtime configuration and input-handling issues but may have limited authenticated and business-logic coverage without deliberate setup.

### Interactive and runtime analysis

IAST combines runtime observation with active tests. Runtime Application Self-Protection can detect or block behaviour in operation, but it is a compensating control rather than a substitute for fixing vulnerabilities.

### Software composition and supply-chain testing

- Inventory dependencies and transitive dependencies.
- Scan for known vulnerabilities and malicious or unexpected packages.
- Verify package provenance, integrity, licenses, and maintainership risk.
- Scan container images, infrastructure code, manifests, and CI workflows.
- Detect secrets in changes and history.
- Generate and retain SBOMs where appropriate.

### Security test focus

Test authentication, account recovery, authorisation, tenant isolation, session management, input handling, injection, cryptography, secrets, logging, privacy, business logic, rate limits, file handling, server-side requests, deserialisation, and administrative paths.

Use threat modelling to identify product-specific abuse cases; generic scanner coverage is not sufficient.

## 19. Penetration testing

Penetration testing is an authorised, goal-driven assessment that attempts to exploit weaknesses and demonstrate impact. It provides a point-in-time sample, not proof that the product is secure.

Use internal or independent testing based on risk, customer requirements, major architectural changes, and incident history. Independence matters most where conflicts of interest or assurance requirements are high.

### Rules of engagement

Obtain written authorisation defining:

- In-scope and excluded systems, accounts, data, locations, and third parties.
- Test dates, contacts, communication paths, and escalation.
- Permitted and prohibited techniques.
- Production safeguards, rate limits, and stop conditions.
- Data handling, evidence encryption, retention, and deletion.
- Social engineering, physical testing, denial of service, persistence, and exfiltration constraints.
- Incident handling and legal approvals.
- Report recipients and disclosure restrictions.

### Lifecycle

1. Scope and threat-model the engagement.
2. Prepare safe accounts, data, monitoring, backups, and contacts.
3. Discover and test according to the rules of engagement.
4. Validate findings and demonstrate impact without unnecessary harm.
5. Report reproducible evidence, severity, affected assets, root cause, and remediation.
6. Triage ownership and target dates.
7. Retest fixes and assess variants or systemic causes.
8. Feed lessons into requirements, design, coding, tests, and monitoring.

The OWASP Web Security Testing Guide is a useful methodology and technique reference for web applications and services.

Source: [OWASP Web Security Testing Guide](https://wstg.owasp.org/)

## 20. Accessibility, usability, and compatibility

- Test with keyboard-only navigation, screen readers, zoom, contrast settings, and other representative assistive technology.
- Include people with disabilities in validation where feasible.
- Verify supported browsers, devices, screen sizes, operating systems, locales, time zones, languages, and input methods.
- Test content clarity, error prevention, recovery, feedback, and cognitive load.
- Automate detectable accessibility rules, then supplement them with manual evaluation; automation cannot assess all accessibility outcomes.
- Define a supported-platform matrix and review it as usage changes.

## 21. Data, privacy, and AI testing

### Test data

- Prefer synthetic data designed for coverage.
- Do not copy production personal data into test environments by default.
- If production-derived data is essential, obtain approval, minimise and transform it, restrict access, enforce retention, and validate re-identification risk.
- Include realistic Unicode, locale, date, scale, skew, null, duplication, and relationship patterns.
- Make test-data creation and cleanup repeatable.

### Data and analytics systems

Test schema, constraints, lineage, completeness, uniqueness, validity, timeliness, reconciliation, transformation invariants, late arrival, duplication, deletion propagation, and access control.

### AI-enabled systems

Define intended use and unacceptable outcomes. Evaluate representative and challenging datasets for accuracy, robustness, bias, privacy, safety, explainability, prompt or tool injection, data leakage, harmful output, and human-oversight effectiveness. Record model, prompt, retrieval data, tool permissions, configuration, and evaluation dataset versions.

Do not rely only on an aggregate score. Examine performance across relevant cohorts, rare cases, adversarial inputs, and high-impact decisions. Monitor production drift and feedback loops.

## 22. Test automation engineering

- Treat test code as production code: review, version, refactor, secure, and own it.
- Give every test a clear purpose and failure message.
- Make tests isolated, repeatable, and order-independent.
- Control time, randomness, concurrency, networks, and external dependencies.
- Use eventual assertions for asynchronous behaviour rather than arbitrary sleeps.
- Keep fixtures small and understandable; use builders or factories for relevant differences.
- Clean up created data, even after failure.
- Parallelise safely and give tests unique resources.
- Quarantine a flaky test only with an owner, reason, and repair deadline; do not silently ignore it.
- Version test tools and environments.
- Run fast checks before expensive suites and select affected tests carefully without losing required coverage.

A test that sometimes passes and sometimes fails under identical relevant conditions is a defect in the test, product, environment, or observability. Investigate rather than normalising reruns.

## 23. Environments and production testing

Test environments should match the production characteristics relevant to the test, not necessarily duplicate all production scale.

- Version infrastructure and configuration.
- Isolate credentials, data, networks, and permissions from production.
- Monitor configuration drift.
- Control shared-environment changes and test-data collisions.
- Use ephemeral environments for isolated change validation where cost permits.
- Preserve a stable environment for release and operational testing when needed.

Production testing can include smoke tests, synthetic monitoring, canaries, shadow traffic, feature flags, and controlled experiments. Protect customers and data with explicit approval, small blast radius, observability, stop conditions, and rollback. Never make destructive test behaviour indistinguishable from real customer activity.

## 24. Defect management

Record enough information to reproduce, understand, prioritise, and verify a defect:

- Clear summary and affected version/environment.
- Preconditions, data, exact steps, and observed result.
- Expected result and source of expectation.
- Reproducibility and scope.
- Logs, screenshots, traces, or minimal failing input with sensitive data removed.
- Severity, business impact, likelihood, and affected users.
- Owner, target, resolution, confirmation result, and related defects.

Separate severity—the consequence of the defect—from priority—the order in which the organisation chooses to address it. Define both consistently.

Fix the underlying cause where feasible. Search for variants, add regression protection, and improve prevention or detection when defects escape repeatedly.

## 25. Release criteria and risk acceptance

Define release criteria before the release is under deadline pressure. Criteria can include:

- Required requirements and risk coverage completed.
- Mandatory automated suites passing on the release candidate.
- No unresolved defects above an agreed severity, unless explicitly accepted.
- Performance, security, accessibility, migration, and recovery objectives met.
- Known issues documented with workarounds and owners.
- Monitoring, alerting, support, rollout, and rollback ready.
- Test evidence reviewed and residual risk accepted by the authorised owner.

Avoid a single universal “100% pass” gate. A skipped critical test and a failed cosmetic test do not carry the same risk. Record exceptions with rationale, compensating controls, owner, and expiry.

## 26. Metrics and reporting

Useful measures include:

- Escaped defects by severity and area.
- Change failure and rollback rate.
- Time to detect, diagnose, repair, and verify.
- Defect recurrence and reopen rate.
- Requirement and risk coverage.
- Test duration, reliability, and flaky-test rate.
- Performance against service objectives.
- Security finding age and retest status.
- Production error, availability, and user-journey success rates.
- Customer-reported quality themes.

Coverage metrics indicate which code, requirements, risks, or configurations were exercised; they do not establish assertion quality or correctness. Use code coverage to find untested areas, not as a standalone target.

Avoid counting test cases, defects, or automation percentage as productivity measures. Such targets encourage low-value tests, duplicate cases, and distorted reporting.

## 27. Common failure modes

- Treating QA as a final testing phase or a separate team’s responsibility.
- Testing only written requirements without validating user need.
- Automating unstable or low-value behaviour indiscriminately.
- An inverted test pyramid dominated by brittle UI tests.
- Excessive mocking that never tests real integration behaviour.
- Happy-path coverage without boundaries, failures, concurrency, or recovery.
- Accepting a rerun as the fix for a flaky test.
- Using production personal data casually in test systems.
- Performance tests without workload models, objectives, or bottleneck telemetry.
- Security scans treated as equivalent to threat modelling or penetration testing.
- Penetration tests without written authorisation and stop conditions.
- Gherkin that describes clicks instead of business behaviour.
- TDD tests coupled to private implementation details.
- Code coverage used as proof of quality.
- Release gates waived informally under schedule pressure.
- Defects fixed without regression tests or systemic follow-up.

## 28. Minimum policy set

- Test strategy defining levels, types, environments, evidence, and risk approach.
- Requirements and acceptance-criteria standard.
- Test automation and test-code standard.
- Defect severity, priority, triage, and exception procedure.
- Performance and capacity testing standard.
- Secure testing and penetration-testing rules.
- Test-data and non-production environment policy.
- Release-readiness and risk-acceptance procedure.
- Production experiment and resilience-testing procedure.

## 29. Suggested implementation order

### First 30 days

- Assign software quality and test ownership and identify critical user and operational journeys.
- Define defect severity and a basic release policy.
- Establish fast unit, integration, and smoke testing in CI.
- Track flaky tests and escaped defects explicitly.
- Identify security, privacy, accessibility, performance, and recovery obligations.
- Stop uncontrolled use of production personal data in test systems.

### Days 31–90

- Create a risk-based product test strategy and trace critical risks to tests.
- Add contract, boundary, failure, authorisation, and migration coverage.
- Establish BDD discovery for ambiguous business rules and TDD where it improves design feedback.
- Define performance objectives and execute a representative baseline.
- Add SAST, dependency, secret, and dynamic security testing.
- Exercise backup restoration, rollback, and major dependency failure.

### Months 4–12

- Add continuous fuzzing for high-risk parsers and input surfaces.
- Commission proportionate independent penetration testing.
- Improve accessibility, usability, compatibility, and operational acceptance.
- Introduce property, mutation, model-based, or chaos testing where they address identified gaps.
- Use production quality signals to refine test priorities.
- Perform root-cause analysis on recurring and escaped defects and improve the development system.

## 30. Evidence checklist

A company should be able to produce:

- Quality objectives, risk assessment, and product test strategy.
- Testable requirements and acceptance criteria.
- Traceability for critical requirements and risks.
- Versioned test code, data definitions, environment configuration, and tool versions.
- CI results, exploratory charters, performance reports, security results, and penetration-test reports.
- Defect records, triage decisions, fixes, confirmation, and regression evidence.
- Release criteria, exceptions, approvals, deployed version, and rollback readiness.
- Backup, recovery, resilience, and operational exercise results.
- Metrics, escaped-defect analysis, corrective actions, and effectiveness reviews.

## References

- [ISO — ISO/IEC 25010:2023](https://committee.iso.org/standard/78176.html)
- [NIST SP 800-218 — Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final)
- [ISTQB — Certified Tester Foundation Level syllabus](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf)
- [OWASP Web Security Testing Guide](https://wstg.owasp.org/)
- [Cucumber — Behaviour-Driven Development](https://cucumber.io/docs/bdd/)
- [Cucumber — Gherkin reference](https://cucumber.io/docs/gherkin/reference/)
- [Cucumber — Writing better Gherkin](https://cucumber.io/docs/bdd/better-gherkin/)
