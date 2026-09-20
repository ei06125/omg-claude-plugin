# Private Data Governance Guide

Last reviewed: 2026-09-19

This guide is a practical starting point for a company that collects, stores, uses, or shares personal data. It is not legal advice. Applicable requirements depend on where the company operates, where individuals are located, the industry, and the data involved.

## 1. Establish scope and accountability

Assign an executive owner for privacy and security. Name operational owners for systems, datasets, vendors, incidents, and individual-rights requests. Decide whether the company is a data controller, processor, or both for every processing activity.

Maintain these records:

- A data inventory covering customer, prospect, employee, contractor, and vendor data.
- A record of processing activities (ROPA): purpose, data categories, individuals affected, lawful basis, recipients, locations, transfers, retention, and safeguards.
- A system and data-flow map showing collection points, services, databases, backups, analytics, subprocessors, and deletion paths.
- A register of applicable laws, contracts, standards, risks, incidents, rights requests, and exceptions.
- Evidence of decisions, reviews, training, testing, and remediation. Accountability means being able to demonstrate compliance, not merely asserting it.

Review the inventory and ROPA when a product, vendor, integration, jurisdiction, or processing purpose changes, and at least annually.

## 2. Apply core privacy principles

Use the GDPR principles as a useful baseline even when GDPR does not apply:

1. **Lawfulness, fairness, and transparency:** identify a valid legal basis and explain processing clearly.
2. **Purpose limitation:** collect data for specific, explicit purposes; assess compatibility before reusing it.
3. **Data minimisation:** collect only what is necessary.
4. **Accuracy:** provide ways to correct data and keep important records current.
5. **Storage limitation:** define and enforce retention periods.
6. **Integrity and confidentiality:** apply appropriate technical and organisational security measures.
7. **Accountability:** document decisions and prove that controls operate effectively.

Do not treat consent as the default legal basis. Depending on the activity, contract, legal obligation, vital interests, public task, or legitimate interests may be more appropriate. Consent must be informed, specific, freely given, unambiguous, recorded, and as easy to withdraw as to give. Sensitive or special-category data requires additional justification and protection.

Source: [European Commission — GDPR principles](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en)

## 3. Determine applicable laws

Obtain jurisdiction-specific advice before launch and expansion. Common regimes to assess include:

- **EU GDPR:** may apply to an EU establishment or to offering goods or services to, or monitoring, people in the EU. It regulates controllers and processors, individual rights, international transfers, security, contracts, and breach reporting.
- **UK GDPR and Data Protection Act 2018:** separate UK regime with its own regulator and transfer mechanisms.
- **United States:** evaluate state privacy laws such as California's CCPA/CPRA and sector rules. HIPAA may apply to protected health information handled by covered entities and business associates; GLBA may apply to financial institutions; COPPA may apply to online services directed to children under 13.
- **Other countries:** many jurisdictions have local registration, representative, localisation, transfer, consent, security, or breach-notification rules.
- **Contractual requirements:** customer security addenda, data-processing agreements, procurement terms, and cyber-insurance conditions can exceed statutory minimums.

Track the location of the company, its staff, infrastructure, vendors, and individuals. Do not infer applicable law solely from where a server is hosted.

Source: [European Commission — GDPR information for organisations](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations_en)

## 4. Build a proportionate management system

### ISO/IEC 27001:2022

ISO/IEC 27001 defines requirements for an Information Security Management System (ISMS). Use it to establish governance, risk assessment, control selection, objectives, internal audits, management review, corrective action, and continuous improvement. Certification is optional unless a customer or contract requires it.

Create a Statement of Applicability explaining which controls apply, which do not, and why. Controls should follow assessed risk rather than becoming a generic checklist.

Source: [ISO — ISO/IEC 27001:2022](https://www.iso.org/standard/27001)

### ISO/IEC 27701:2025

ISO/IEC 27701 defines requirements and guidance for a Privacy Information Management System (PIMS). The 2025 edition is a standalone management-system standard that can also align with ISO/IEC 27001. It is intended for organisations acting as PII controllers or processors.

Use it to formalise privacy roles, risk management, controller/processor obligations, evidence, audits, and continual improvement. Certification can demonstrate maturity, but it does not by itself prove compliance with every law.

Source: [ISO — ISO/IEC 27701:2025](https://committee.iso.org/standard/27701)

### Supporting standards and frameworks

- **ISO/IEC 27002:** implementation guidance for information-security controls.
- **ISO/IEC 27017:** cloud-security controls for cloud customers and providers.
- **ISO/IEC 27018:2025:** protection of PII in public cloud processing.
- **ISO/IEC 29100:** privacy framework and common privacy principles.
- **ISO/IEC 29134:** guidance for privacy impact assessments.
- **NIST Privacy Framework:** voluntary, risk-based privacy outcomes organised around governance and operational functions.
- **NIST Cybersecurity Framework 2.0:** cybersecurity governance and risk outcomes.
- **SOC 2:** independent attestation against selected Trust Services Criteria; often commercially useful for service providers, but not a privacy law or ISO certification.
- **PCI DSS:** required by relevant payment-card contracts when storing, processing, or transmitting cardholder data. Prefer using a compliant payment provider to reduce scope.

Sources: [ISO security and privacy package](https://www.iso.org/publication/PUB200277.html), [NIST Privacy Framework](https://www.nist.gov/privacy-framework)

## 5. Adopt the minimum policy set

Policies should state their owner, approver, scope, responsibilities, mandatory rules, exceptions, evidence, review interval, and enforcement. Start with:

- **External privacy notice:** collected data, sources, purposes, legal bases, sharing, transfers, retention, rights, complaints, contact details, and automated decision-making where relevant.
- **Internal privacy and data-protection policy:** responsibilities and handling rules throughout the data lifecycle.
- **Information-security policy:** security objectives, governance, risk ownership, and control requirements.
- **Data classification and handling policy:** classification levels, labelling, allowed storage and transmission, sharing, and disposal.
- **Retention and deletion policy:** periods or decision criteria for each record class, legal holds, backup handling, and verifiable deletion.
- **Access-control policy:** least privilege, MFA, privileged access, periodic reviews, service accounts, and joiner/mover/leaver procedures.
- **Incident-response and breach-notification plan:** roles, severity, evidence preservation, containment, legal assessment, communications, notification deadlines, exercises, and lessons learned.
- **Individual-rights request procedure:** identity verification, request logging, search, exemptions, response, deletion propagation, and deadlines.
- **Vendor and subprocessor policy:** due diligence, approval, contract requirements, monitoring, change notification, and exit/deletion.
- **Secure development policy:** threat modelling, code review, dependency management, testing, secrets handling, logging, and vulnerability remediation.
- **Acceptable-use and remote-work policies:** approved systems, devices, communications, storage, monitoring, and reporting.
- **Backup and business-continuity policy:** encrypted backups, restoration tests, recovery objectives, access, retention, and deletion implications.
- **AI and automated-processing policy:** approved uses, prohibited inputs, vendor review, human oversight, accuracy, explainability, intellectual property, and retention.

Keep policies short enough to use. Put detailed implementation requirements in standards and repeatable steps in procedures.

## 6. Engineer privacy and security into products

Before implementing a feature, document the purpose, data needed, lawful basis, users affected, risks, and deletion behavior. Use privacy-protective defaults.

Minimum technical controls:

- Encrypt data in transit with current TLS and encrypt sensitive data at rest.
- Centralise identity, require MFA, apply least privilege, and review access periodically.
- Separate production from development; do not use raw production personal data in tests unless specifically justified and protected.
- Store secrets in a secret-management system, not source code, images, logs, tickets, or chat.
- Minimise logs and telemetry. Redact credentials, tokens, identifiers, message bodies, and sensitive fields.
- Define security-relevant audit events and protect logs against unauthorised access and alteration.
- Validate inputs and outputs, patch dependencies and infrastructure, scan continuously, and prioritise remediation by risk.
- Use pseudonymisation or aggregation where direct identity is unnecessary. Keep re-identification keys separate.
- Make deletion an end-to-end capability covering primary stores, search indexes, caches, analytics, vendors, and backup expiry.
- Test backup restoration, incident response, rights requests, and deletion—not only their documented procedures.

### gRPC-specific controls

If “gRPC” was intended rather than “GDPR”:

- Use TLS for all network traffic and mutual TLS for service-to-service trust where appropriate.
- Authenticate callers and authorise each RPC method and resource; network location alone is not identity.
- Propagate identity using short-lived, audience-restricted credentials. Do not place secrets or unnecessary personal data in metadata.
- Validate protobuf messages, enum values, identifiers, sizes, nesting depth, and business invariants.
- Configure message-size limits, deadlines, concurrency limits, rate limits, retries, and circuit breaking. Avoid retrying non-idempotent operations without an idempotency design.
- Prevent sensitive request and response bodies, authorization metadata, and tokens from entering logs or traces.
- Inventory services and methods; version contracts and review backward-compatibility and data-exposure changes.
- Secure reflection and health endpoints; restrict or disable them in production when not operationally required.

Source: [gRPC — Authentication](https://grpc.io/docs/guides/auth/)

## 7. Manage high-risk processing

Perform a Data Protection Impact Assessment (DPIA) before processing likely to create high risk, such as large-scale sensitive data, systematic monitoring, biometrics, location tracking, children’s data, consequential profiling, novel technology, or combining datasets in unexpected ways.

A DPIA should describe the processing, necessity and proportionality, individuals and risks, mitigations, residual risk, approvals, and review triggers. Stop or redesign processing whose residual risk is unacceptable. Seek regulator consultation where legally required.

Source: [ICO — Data protection by design and default](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/data-protection-by-design-and-by-default/)

## 8. Respect individual rights

Create a documented workflow for access, correction, deletion, restriction, objection, portability, consent withdrawal, and challenges to automated decisions where applicable.

The workflow should:

1. Accept requests through accessible channels.
2. Authenticate proportionately without collecting excessive identity data.
3. Log receipt and calculate the legal deadline.
4. Search all relevant systems and subprocessors.
5. Review third-party rights, privilege, retention duties, and applicable exemptions.
6. Respond securely in clear language.
7. Propagate corrections, restrictions, or deletion and retain limited evidence of completion.

Exercise the process with test requests before a real deadline applies.

## 9. Control vendors and international transfers

Before sharing personal data, establish the parties' roles and execute an appropriate data-processing agreement. It should cover documented instructions, confidentiality, security, subprocessors, rights assistance, breaches, audits, return/deletion, and regulatory cooperation.

For every vendor:

- Record the service, owner, data, purpose, locations, subprocessors, access, retention, and exit plan.
- Assess security and privacy proportionately to the risk; verify important claims with reports or evidence.
- Restrict use of company data for advertising, unrelated analytics, or vendor model training unless deliberately approved and disclosed.
- Monitor material changes and incidents.
- Confirm return or deletion at termination.

For international transfers, document an approved transfer mechanism and any required transfer risk assessment and supplementary safeguards. Vendor location, support access, and subprocessor locations all matter.

## 10. Prepare for incidents and breaches

An incident is not limited to hacking. Loss, accidental disclosure, unauthorised access, corruption, and unavailability can all be personal-data breaches.

Maintain a response process that can quickly determine:

- What happened and when the company became aware.
- Systems, individuals, data categories, volume, and jurisdictions affected.
- Whether confidentiality, integrity, or availability was compromised.
- Likely consequences and risk to individuals.
- Containment, recovery, evidence, and prevention measures.
- Contractual, insurer, law-enforcement, regulator, customer, and individual notifications.

Under GDPR, a controller must notify the competent supervisory authority without undue delay and, where the breach is likely to risk individuals' rights and freedoms, no later than 72 hours after awareness. High-risk breaches may also require notice to affected individuals. Processors must notify controllers without undue delay. Record the assessment even when notification is not required.

Source: [European Commission — Data-protection obligations and breach notification](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations_en)

## 11. Measure effectiveness

Report a small set of decision-useful metrics to leadership:

- Percentage of systems and processing activities with current owners and records.
- Overdue retention deletion and access reviews.
- Rights-request volume, age, and on-time completion.
- Vendor reviews and high-risk findings outstanding.
- Incidents by severity, detection time, containment time, and corrective-action status.
- Critical vulnerabilities and remediation age.
- Staff training completion and exercise results.
- DPIAs, exceptions, and risks awaiting approval or treatment.

Use internal audits and management reviews to verify that controls operate, not merely that documents exist. Record corrective actions, owners, due dates, and effectiveness checks.

## 12. Suggested implementation order

### First 30 days

- Assign accountable owners.
- Identify applicable jurisdictions and contractual obligations.
- Inventory data, systems, vendors, and data flows.
- Eliminate obviously unnecessary collection and public exposure.
- Establish incident contacts and a basic response plan.
- Publish an accurate privacy notice.

### Days 31–90

- Complete the ROPA, lawful-basis assessment, retention schedule, vendor register, and core policies.
- Implement MFA, least privilege, encryption, secrets management, backup testing, and security logging.
- Establish rights-request, vendor-review, vulnerability, and breach workflows.
- Perform DPIAs for high-risk existing processing.

### Months 4–12

- Select an ISMS/PIMS framework and conduct a formal risk assessment.
- Define control owners, evidence, metrics, internal audit, and management review.
- Exercise incident response, recovery, deletion, and rights workflows.
- Remediate gaps and decide whether ISO certification or SOC 2 attestation has business value.

## 13. Minimum evidence checklist

A company should be able to produce:

- Data inventory, ROPA, and data-flow diagrams.
- Applicable-requirements register and documented legal bases.
- Approved policies, standards, procedures, and training records.
- Risk register, treatment plan, DPIAs, and approved exceptions.
- Access reviews, vulnerability results, restoration tests, and incident exercises.
- Vendor assessments, agreements, subprocessor list, and transfer records.
- Rights-request and incident logs with timely decisions.
- Retention schedule and evidence of deletion.
- Audit results, management-review minutes, corrective actions, and follow-up evidence.

## References

- [European Commission — Data protection](https://commission.europa.eu/law/law-topic/data-protection_en)
- [European Commission — GDPR principles](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en)
- [European Commission — Organisational obligations](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations_en)
- [ISO — ISO/IEC 27001:2022](https://www.iso.org/standard/27001)
- [ISO — ISO/IEC 27701:2025](https://committee.iso.org/standard/27701)
- [NIST — Privacy Framework](https://www.nist.gov/privacy-framework)
- [ICO — Accountability and governance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/)
- [gRPC — Authentication](https://grpc.io/docs/guides/auth/)
