# Identity, Access, and Security Governance Guide

Last reviewed: 2026-09-19

This guide is a practical baseline for a company designing identity and access management (IAM). It covers the CIA security objectives, AAA control model, RBAC, SSO, SAML, OAuth, OpenID Connect, provisioning, privileged access, and operating controls. It is not a substitute for a threat model, risk assessment, or requirements specific to a regulated industry.

## 1. Security objectives: the CIA triad

Security decisions should state which objective they protect and how failure affects the business.

### Confidentiality

Information is available only to authorised subjects. Controls include authentication, authorisation, encryption, data classification, secrets management, network protection, and restrictions on exports and logs.

Examples of failure include an exposed database, an employee reading records outside their duties, or an access token appearing in application logs.

### Integrity

Information and systems remain accurate, complete, authentic, and protected from unauthorised modification or destruction. Controls include digital signatures, hashes, validated transactions, separation of duties, change control, immutable audit records, concurrency controls, and tested restoration.

Examples of failure include unauthorised bank-detail changes, modified software artifacts, or an administrator altering audit records.

### Availability

Authorised users can reliably access information and services when needed. Controls include redundancy, capacity management, rate limiting, denial-of-service protection, backups, disaster recovery, monitoring, and tested recovery procedures.

Examples of failure include an unavailable identity provider blocking every application, expired signing keys causing login failures, or destructive actions that cannot be recovered.

The objectives can conflict. Strong confidentiality controls that introduce a single identity-provider dependency may reduce availability. Highly available replicas may expand confidentiality exposure. Document the trade-off and match controls to business impact.

## 2. Access-control functions: AAA

AAA commonly means authentication, authorisation, and accounting.

1. **Authentication:** verifies an asserted identity or control of an authenticator. It answers “who or what is requesting access?” Authentication does not grant permission.
2. **Authorisation:** evaluates whether the authenticated subject may perform an action on a resource under current conditions. It answers “is this action allowed?”
3. **Accounting:** records security-relevant activity so the company can attribute actions, detect misuse, investigate incidents, meet retention requirements, and demonstrate control operation. It is also called auditing in some contexts.

Keep these functions separate. A valid login is not sufficient authorisation. A permitted action without a reliable audit trail weakens detection and accountability.

For each important request, aim to record: subject, acting identity, authentication context, action, resource, decision, policy or role used, time, source, correlation identifier, and result. Exclude passwords, private keys, raw tokens, session cookies, and unnecessary personal or sensitive payloads.

## 3. IAM governance model

Assign clear owners:

- **Identity owner:** establishes authoritative identity sources and lifecycle rules.
- **Application owner:** defines application roles, sensitive operations, and review requirements.
- **Data or resource owner:** approves access according to business need and data classification.
- **IAM/security team:** operates identity providers, policy systems, privileged-access controls, integrations, and monitoring.
- **Managers:** validate workforce access and promptly report lifecycle changes.
- **Human resources or contractor management:** provides authoritative joiner, mover, and leaver events.
- **Audit/compliance:** independently tests design and effectiveness.

Maintain inventories of identities, identity providers, applications, roles, entitlements, groups, service accounts, privileged accounts, federation connections, signing and encryption keys, exceptions, and access owners.

Define one authoritative source for each identity class. Avoid multiple systems independently creating or disabling the same workforce identity.

## 4. Identity lifecycle

### Joiners

- Verify the identity to the assurance appropriate for the role and risk.
- Create one attributable account per person; do not share user accounts.
- Assign baseline access from approved attributes such as employment type, department, and location.
- Require additional approval for privileged, production, financial, or sensitive-data access.
- Enrol phishing-resistant MFA wherever feasible and issue recovery methods securely.
- Communicate acceptable-use and security obligations before access begins.

### Movers

- Treat role, department, manager, location, and employment-type changes as access-review events.
- Remove obsolete access before or when new access is granted; do not only accumulate permissions.
- Re-evaluate segregation-of-duties conflicts and privileged access.
- Apply time limits to transitional access.

### Leavers

- Disable interactive access at the effective termination time, immediately for high-risk departures.
- Revoke sessions, tokens, API keys, certificates, VPN access, recovery methods, and registered devices as applicable.
- Rotate shared secrets that the individual knew.
- Transfer ownership of data, automation, repositories, and business records.
- Preserve required records and remove access from downstream applications through automated deprovisioning plus verification.

### Dormant and exceptional identities

Disable or investigate dormant accounts. Give guests, contractors, interns, bots, test users, break-glass accounts, and merger/acquisition identities explicit sponsors, expiry dates, and narrower defaults.

## 5. Authentication

Use the current NIST SP 800-63-4 suite as a risk-based reference for identity proofing, authenticator management, and federation. It separates Identity Assurance Level (IAL), Authentication Assurance Level (AAL), and Federation Assurance Level (FAL), allowing each to match the transaction risk.

Source: [NIST — SP 800-63 Digital Identity Guidelines](https://www.nist.gov/identity-access-management/projects/nist-special-publication-800-63-digital-identity-guidelines)

### Authentication requirements

- Require MFA for workforce users, administrators, remote access, source control, cloud control planes, production, and sensitive customer functions.
- Prefer phishing-resistant authenticators such as FIDO2/WebAuthn security keys or platform passkeys. Use weaker methods only after documenting the risk and transition plan.
- Treat SMS and voice OTP as weaker recovery or transitional methods because of interception and account-takeover risks.
- Do not use security questions or knowledge about a person as an authentication factor.
- Screen new passwords against common, compromised, and context-specific blocklists.
- Permit long passwords and password-manager use. Do not impose composition rules that predictably transform passwords.
- Do not force arbitrary periodic password changes without evidence of compromise or another risk-based reason.
- Rate-limit failed attempts and detect credential stuffing without creating an easy denial-of-service mechanism.
- Protect enrolment, authenticator replacement, and account recovery as strongly as normal authentication. Recovery is frequently the weakest path.
- Notify users of important authentication, recovery, and credential changes.

### Step-up and reauthentication

Require fresh or stronger authentication for high-risk actions such as changing authenticators, exporting sensitive data, viewing recovery codes, modifying payment details, elevating privilege, deleting an organisation, or accessing unusual volumes of records.

Risk signals such as device posture, location, network, impossible travel, and anomalous behaviour can trigger additional verification. They should supplement, not silently replace, sound authentication and authorisation.

## 6. Authorisation models

### Role-Based Access Control (RBAC)

RBAC assigns permissions to roles and roles to users. Roles should reflect stable job functions or application responsibilities rather than individual people.

Use RBAC when permissions group naturally by job or responsibility. A sound role design includes:

- A documented purpose, owner, scope, permissions, eligibility, and review interval.
- Separate business roles from technical entitlements where practical.
- Deny-by-default behaviour.
- Least privilege and no direct user permissions except controlled exceptions.
- Separation of duties for conflicting activities.
- Role assignment approval by the appropriate manager and resource owner.
- Expiry for temporary roles and just-in-time activation for privileged roles.
- Periodic review of role definitions as well as user-role assignments.

Avoid role explosion. Creating a role for every minor variation makes governance harder than direct permissions. Avoid broad roles such as `admin`, `power-user`, or `developer` without a precise permission contract.

Sources: [NIST — RBAC definition](https://csrc.nist.gov/glossary/term/role_based_access_control), [NIST — RBAC project](https://csrc.nist.gov/projects/role-based-access-control)

### Attribute-Based Access Control (ABAC)

ABAC evaluates subject, resource, action, and environmental attributes. Examples include department, tenant, data classification, resource owner, device compliance, time, and location.

Use ABAC for contextual or fine-grained policies that RBAC cannot model cleanly. Govern attribute sources carefully: stale, user-controlled, or ambiguous attributes create authorisation vulnerabilities. Policies must have tests, version control, owners, decision logs, and safe failure behaviour.

### Relationship- and policy-based control

Relationship-Based Access Control (ReBAC) grants access through relationships such as owner, member, parent organisation, or document collaborator. Policy-Based Access Control centralises decision rules and can combine roles, attributes, relationships, and context.

Use a hybrid model where appropriate: RBAC for broad job capabilities, ABAC/ReBAC for resource- and context-specific decisions.

### Mandatory and discretionary control

Mandatory Access Control (MAC) uses centrally enforced classifications and clearances and is common in high-assurance environments. Discretionary Access Control (DAC) lets resource owners delegate access. DAC is flexible but needs sharing constraints, visibility, expiry, and review.

## 7. Least privilege and separation of duties

- Grant only the actions, resources, environments, and duration required.
- Separate ordinary and administrative accounts.
- Require just-in-time, time-bounded elevation for production and critical administration.
- Require independent approval for high-impact changes and financial transactions.
- Prevent one person from requesting, approving, executing, and concealing the same sensitive action.
- Review both toxic combinations and paths that indirectly produce them through nested groups or multiple roles.
- Remove unused privileges based on role changes and observed use, after validating that telemetry is complete.
- Use break-glass access only for emergencies; protect it with strong controls, test it, alert on every use, and review use immediately.

Zero trust means no implicit trust based only on network location or device ownership. Authenticate and authorise subject and device before access, and make least-privilege decisions per resource and request where risk warrants it.

Source: [NIST SP 800-207 — Zero Trust Architecture](https://csrc.nist.gov/pubs/sp/800/207/final)

## 8. Single sign-on and federation

### SSO

Single sign-on lets a user authenticate through a central identity provider (IdP) and access multiple service providers or relying parties. Benefits include central MFA, faster deprovisioning, fewer application passwords, consistent conditional access, and stronger visibility.

SSO concentrates risk. An IdP compromise, federation misconfiguration, or outage can affect every connected service. Protect the IdP as critical infrastructure with dedicated administration, phishing-resistant MFA, configuration review, resilient recovery, restricted integrations, signing-key protection, monitoring, and tested emergency access.

SSO is an experience and architecture, not a protocol. Common federation protocols are SAML and OpenID Connect.

### SAML 2.0

SAML conveys XML assertions about authentication, attributes, and authorisation between an IdP and service provider (SP). It is widely used for enterprise browser SSO.

Implementation requirements:

- Use maintained SAML libraries; do not implement XML signature validation yourself.
- Validate the XML signature against explicitly trusted IdP keys.
- Validate issuer, audience, recipient, destination, assertion time bounds, and request correlation.
- Accept only expected algorithms, bindings, endpoints, and assertion types.
- Protect against XML Signature Wrapping by ensuring the validated signed element is exactly the element consumed.
- Reject unsigned assertions or responses unless a rigorously assessed profile explicitly permits them.
- Use short assertion lifetimes and replay detection where supported.
- Protect SP-initiated state such as `RelayState` against tampering and open redirects.
- Minimise attributes in assertions and define stable identifiers deliberately.
- Plan signing-certificate rollover with overlap, metadata validation, monitoring, and rollback.
- Do not confuse Single Logout with guaranteed termination of every local application session; test actual behaviour.

Source: [OASIS — SAML 2.0 standard](https://www.oasis-open.org/standard/saml/)

### OpenID Connect

OpenID Connect (OIDC) is an authentication layer built on OAuth 2.0. It returns an ID Token describing an authentication event and commonly provides user claims. OAuth grants delegated access; OIDC authenticates users. An access token is for an API, while an ID Token is for the client. Do not use an ID Token as an API bearer token.

Implementation requirements:

- Use Authorization Code flow with PKCE using `S256`.
- Validate ID Token signature, issuer, audience, expiry, issued-at constraints, and `nonce`; validate authorised-party claims when applicable.
- Use exact pre-registered redirect URI matching and prevent open redirects.
- Obtain configuration and keys from trusted issuer metadata; restrict accepted issuers and algorithms.
- Cache signing keys safely and handle rotation without accepting untrusted key sources.
- Request the minimum scopes and claims.
- Establish a stable account-linking rule. Do not link solely on an unverified or mutable email address.
- Bind login state to the initiating browser session and prevent login CSRF and mix-up attacks.

Source: [OpenID Foundation — OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

### OAuth 2.0

OAuth 2.0 is an authorisation framework for delegated API access. It is not by itself a login protocol.

Current best practices include:

- Use Authorization Code flow with PKCE for browser and native clients; do not use the implicit grant.
- Compare redirect URIs using exact matching and prohibit open redirectors.
- Use transaction-specific `state` or equivalent CSRF protection and OIDC `nonce` where applicable.
- Give access tokens narrow audience, scope, privilege, and lifetime.
- Rotate refresh tokens or sender-constrain them; detect replay and revoke the token family when reuse indicates theft.
- Prefer asymmetric client authentication for confidential clients where feasible.
- Never put tokens in URLs or logs. Store browser tokens to minimise exposure to injected scripts.
- Validate token issuer, audience, signature, time constraints, and intended token type at each resource server.
- Consider sender-constrained access tokens using mTLS or DPoP for higher-risk APIs.
- Keep resource-owner password and implicit grants disabled.

Source: [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/info/rfc9700/)

## 9. Provisioning and deprovisioning with SCIM

System for Cross-domain Identity Management (SCIM) standardises user and group provisioning between identity systems and applications. SSO does not automatically provision or deprovision accounts; pair federation with SCIM or an equivalent controlled lifecycle integration.

- Authenticate and authorise SCIM clients strongly and restrict them to the intended tenant.
- Minimise writable attributes and prevent privilege escalation through group or role mappings.
- Define whether disable, suspend, soft-delete, and delete have different effects.
- Make operations idempotent and monitor failures, drift, and reconciliation results.
- Treat group membership changes as access changes and audit them.
- Protect SCIM bearer tokens or client credentials as high-impact secrets and rotate them.
- Test termination end to end, including downstream sessions and locally retained privileges.

Source: [RFC 7644 — SCIM Protocol](https://www.rfc-editor.org/info/rfc7644/)

## 10. Machine and workload identities

Service accounts, applications, workloads, devices, automation, and CI/CD systems require the same lifecycle discipline as people.

- Give every workload a unique, attributable identity; do not share a universal service credential.
- Prefer short-lived, automatically issued credentials based on workload identity over static API keys.
- Restrict credentials by audience, service, environment, operation, and network context where useful.
- Store remaining secrets in a managed secrets system; never in source, build logs, container images, tickets, or chat.
- Rotate automatically and verify that old credentials stop working.
- Assign an owner and expiry or review date to every non-human identity.
- Prevent service identities from interactive login unless explicitly required.
- Review machine permissions and usage; detect credentials used from unexpected workloads or environments.

## 11. Privileged Access Management

Privileged Access Management (PAM) should cover cloud administrators, domain administrators, database administrators, production access, security tooling, secrets platforms, CI/CD, and emergency accounts.

Minimum controls:

- Separate privileged and routine identities.
- Phishing-resistant MFA and managed administrative devices.
- Just-in-time and time-bound elevation with a ticket, purpose, and approval according to risk.
- Credential vaulting or ephemeral credentials instead of manually shared secrets.
- Session and command auditing proportionate to sensitivity, with privacy safeguards.
- Immediate alerting for emergency access, policy changes, logging disablement, and creation of new administrators.
- Regular review of standing privilege, nested paths, and inactive administrators.
- Dual control for root-of-trust operations such as IdP recovery, key export, and audit-log deletion.

## 12. Session and token security

- Use secure, unpredictable session identifiers and rotate them after authentication and privilege changes.
- Put browser sessions in cookies with `Secure`, `HttpOnly`, and an appropriate `SameSite` setting.
- Enforce inactivity and absolute lifetime based on risk; require reauthentication for sensitive actions.
- Revoke or constrain sessions when users leave, authenticators change, risk increases, or privilege is removed.
- Do not embed secrets or unnecessary personal data in tokens. Signed JWT contents are readable unless separately encrypted.
- Keep tokens small and claims stable. Avoid putting rapidly changing authorisation data in long-lived self-contained tokens.
- Define clock-skew tolerance narrowly and synchronise system clocks.
- Keep signing keys in managed key systems, restrict use, rotate them, publish required metadata safely, and rehearse emergency rollover.

## 13. Logging, detection, and accounting

Centralise and protect logs for:

- Successful and failed authentication, MFA challenges, recovery, and authenticator changes.
- Session creation, refresh, revocation, and unusual token use.
- Role, group, entitlement, policy, and federation configuration changes.
- Privilege elevation and privileged actions.
- Identity creation, disablement, deletion, and authoritative-source changes.
- Access denials, high-value reads or exports, and break-glass use.
- Signing-key, secret, and certificate lifecycle events.

Synchronise time, use correlation identifiers, restrict log access, detect tampering, and retain records according to legal and operational requirements. Alert on patterns such as impossible travel, password spraying, MFA fatigue, dormant-account use, privilege escalation, disabled logging, unusual data access, and machine credentials used from new locations.

Logs support investigation but may themselves contain personal or sensitive data. Apply minimisation, access controls, retention, and redaction.

## 14. Access reviews and control testing

Review access according to risk, not one universal interval. Privileged, production, financial, and highly sensitive access should receive more frequent scrutiny.

A useful certification process shows reviewers:

- The exact effective permissions, not only friendly role names.
- Why access was granted, its owner, last use, and expiry.
- Nested groups, inherited permissions, service accounts, and toxic combinations.
- A clear choice to approve, modify, or revoke with recorded justification.

Verify removals after the review. Measure reviewer quality and late decisions; a completed rubber-stamp campaign provides little assurance.

Test controls by attempting expected allow and deny cases, termination, role changes, token revocation, certificate rollover, IdP outage, emergency access, and recovery. Include authorisation tests in application CI/CD, especially tenant isolation and object-level permissions.

## 15. Common failure modes

- Checking authentication but not object-level or tenant-level authorisation.
- Trusting roles or tenant identifiers supplied by the client.
- Making hidden UI elements the only authorisation control.
- Giving every employee or developer broad access “temporarily.”
- Leaving local accounts enabled after introducing SSO.
- Assuming SSO logout revokes all application sessions and API tokens.
- Linking federated accounts by unverified email address.
- Accepting tokens meant for another audience, issuer, environment, or token type.
- Long-lived API keys without owners, expiry, rotation, or usage monitoring.
- Group nesting that creates invisible privilege escalation.
- Delayed or failed downstream deprovisioning.
- Emergency accounts that are untested, overused, or unaudited.
- Logging tokens, cookies, passwords, SAML assertions, or sensitive claims.
- Treating network location as proof of identity or permission.

## 16. Minimum policy set

- IAM policy covering identity classes, lifecycle, assurance, federation, and ownership.
- Access-control standard defining least privilege, RBAC/ABAC patterns, approvals, and review frequency.
- Authentication standard defining MFA, authenticators, password handling, recovery, and reauthentication.
- Privileged-access policy defining separate accounts, elevation, emergency use, and monitoring.
- Service-account and secrets-management standard.
- Federation and SSO standard for SAML, OIDC, keys, claims, integrations, and local-account exceptions.
- Logging and monitoring standard defining required events, protection, retention, alerting, and privacy.
- Joiner/mover/leaver procedure with target completion times and verification.
- Access-review and segregation-of-duties procedure.
- Exception process with risk acceptance, compensating controls, owner, and expiry.

## 17. Suggested implementation order

### First 30 days

- Assign IAM owners and inventory identity stores, applications, administrators, service accounts, and federation connections.
- Enforce MFA on email, source control, cloud platforms, finance, HR, remote access, and administrative accounts.
- Remove shared human accounts and close known dormant or orphaned access.
- Establish rapid leaver handling and emergency access.
- Centralise important authentication and administrative logs.

### Days 31–90

- Select one primary workforce IdP and integrate high-risk applications with SSO.
- Define baseline roles, sensitive privileges, approval paths, and review schedules.
- Automate provisioning and deprovisioning with SCIM or equivalent integrations.
- Introduce privileged elevation and separate administrative accounts.
- Establish authentication, federation, access-control, and service-account standards.
- Test tenant and object-level authorisation in critical applications.

### Months 4–12

- Expand phishing-resistant MFA and retire weaker factors where feasible.
- Reduce standing privilege with just-in-time access.
- Replace static workload secrets with short-lived identities.
- Implement contextual policies where they materially reduce risk.
- Exercise IdP outage, signing-key rollover, account recovery, and break-glass procedures.
- Measure and remediate role growth, access-review quality, deprovisioning latency, and orphaned identities.

## 18. Evidence and metrics

Keep evidence of:

- Identity, application, entitlement, federation, and service-account inventories.
- Approved role and policy definitions with owners and version history.
- Joiner/mover/leaver events and completed downstream actions.
- Access requests, approvals, expiry, elevation, and revocation.
- Access reviews and verified remediation.
- MFA coverage by identity and application risk.
- Federation metadata, key rotation, integration tests, and exception decisions.
- Authentication, authorisation, and privileged-action audit trails.
- Recovery, break-glass, IdP outage, and deprovisioning exercises.

Useful metrics include:

- MFA and phishing-resistant MFA coverage.
- Median and maximum termination-to-revocation time.
- Privileged accounts and standing privileged assignments.
- Dormant, orphaned, shared, and ownerless identities.
- Service credentials older than policy permits.
- Applications using central SSO and automated deprovisioning.
- Access reviews completed on time and privileges removed.
- Authentication failures, recovery events, and detected account takeovers.
- Authorisation defects, especially cross-tenant and object-level failures.

## References

- [NIST — SP 800-63-4 Digital Identity Guidelines](https://www.nist.gov/identity-access-management/projects/nist-special-publication-800-63-digital-identity-guidelines)
- [NIST — Role-Based Access Control](https://csrc.nist.gov/projects/role-based-access-control)
- [NIST SP 800-207 — Zero Trust Architecture](https://csrc.nist.gov/pubs/sp/800/207/final)
- [OASIS — SAML 2.0](https://www.oasis-open.org/standard/saml/)
- [OpenID Foundation — OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/info/rfc9700/)
- [RFC 7644 — SCIM Protocol](https://www.rfc-editor.org/info/rfc7644/)
