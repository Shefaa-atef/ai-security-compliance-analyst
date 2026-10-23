import { requirements } from "./requirements";
const explanations = [
  [
    "needs_clarification",
    [],
    "The team is named, but an accountable business owner is not identified.",
    "Assign a named business owner before deployment.",
  ],
  [
    "needs_clarification",
    [
      "The system will process customer names, account information, support tickets, and conversation history.",
    ],
    "Sensitive customer information is involved. Data protection controls are not described.",
    "Confirm data minimization, redaction, retention, and provider data-handling controls.",
  ],
  [
    "supported",
    [
      "A human support agent will review the generated response before sending it to the customer.",
    ],
    "A person reviews each customer-facing response before use.",
    "Document reviewer responsibilities and escalation procedures.",
  ],
  [
    "needs_clarification",
    [],
    "The scenario does not describe logging or monitoring.",
    "Define audit events, retention, redaction, and monitoring responsibilities.",
  ],
  [
    "needs_clarification",
    [],
    "User authentication and authorization are not described.",
    "Define approved users and least-privilege access.",
  ],
  [
    "needs_clarification",
    ["The application will use a third-party hosted LLM API."],
    "A third-party service is involved, but its assessment status is unknown.",
    "Complete the provider security assessment and review contractual safeguards.",
  ],
  [
    "needs_clarification",
    [
      "A customer support team wants to use an LLM to summarize customer conversations and suggest responses to support agents.",
    ],
    "The intended task is described, but documented limitations are not provided.",
    "Document allowed uses, known limitations, and prohibited uses.",
  ],
  [
    "needs_clarification",
    [],
    "Customer financial information warrants risk review; no review outcome is provided.",
    "Have governance determine the risk classification and required review before deployment.",
  ],
];
export const sampleAssessment = {
  assessment_id: "sample-customer-support",
  summary:
    "Human review is a strong starting point. Before deployment, clarify how customer information is protected and who is accountable for the service.",
  risk_level: "high",
  risk_rationale:
    "Illustrative high-risk rating because customer account information will be processed by an external AI provider. A governance reviewer must confirm the classification.",
  findings: requirements.map((item, index) => ({
    requirement_id: item.id,
    status: explanations[index][0],
    evidence: explanations[index][1],
    explanation: explanations[index][2],
    recommendation: explanations[index][3],
  })),
  next_actions: [
    "Identify the accountable business owner.",
    "Confirm data controls and complete the provider security assessment.",
    "Document access, monitoring, limitations, and the required governance review.",
  ],
  follow_up_questions: [
    "What customer information will leave the organization?",
    "Has the model provider completed a security assessment?",
    "Who owns the application and approves it for deployment?",
  ],
  review_steps: [
    "Scenario facts identified",
    "Eight governance requirements reviewed",
    "Evidence and missing information mapped",
    "Recommended actions prepared",
  ],
};
