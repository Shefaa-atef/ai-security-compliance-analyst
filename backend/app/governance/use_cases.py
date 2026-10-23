"""The three example use cases supplied with the business scenario.

Shared by the tests and the live check so the wording is defined once.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class UseCase:
    id: str
    title: str
    text: str


CUSTOMER_SUPPORT = UseCase(
    "A",
    "Customer Support Assistant",
    "A customer support team wants to use an LLM to summarize customer conversations and suggest "
    "responses to support agents. The system will process customer names, account information, support "
    "tickets, and conversation history. A human support agent will review the generated response before "
    "sending it to the customer. The application will use a third-party hosted LLM API.",
)

SECURITY_ASSISTANT = UseCase(
    "B",
    "Internal Security Assistant",
    "The cybersecurity team wants to deploy an internal AI assistant that can analyze security alerts "
    "and recommend investigation steps. The assistant will have access to internal security logs and "
    "selected threat intelligence sources. Security analysts will review recommendations before taking "
    "action. The system will be deployed within the organization's cloud environment.",
)

HR_PROMOTIONS = UseCase(
    "C",
    "Automated Employee Decisions",
    "HR wants to use an AI system to analyze employee performance information and automatically "
    "recommend employees for promotion. The system will process employee performance records and HR "
    "information. HR intends for the AI system's recommendation to be used as the primary input into "
    "promotion decisions.",
)

USE_CASES: tuple[UseCase, ...] = (CUSTOMER_SUPPORT, SECURITY_ASSISTANT, HR_PROMOTIONS)
