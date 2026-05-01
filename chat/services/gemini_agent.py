"""
Gemini AI agent (LangChain) that converts natural-language Hindi/English
instructions into preview proposals across customer ledger transactions,
supplier payments, and worker attendance, AND answers read-only questions
about customer balances, project expenses, and supplier dues.

Uses LangChain's create_tool_calling_agent + AgentExecutor with Google
Gemini 2.5 Flash. The propose_* tools return preview payloads that the
caller (views.py) persists as a PendingTransaction and shows to the user
for confirmation.
"""
import json
import logging
import os
from datetime import date
from typing import Dict, List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

# `langchain_google_genai` is an optional install. Import it lazily inside
# _build_llm() so that loading this module (e.g. during Django URL config
# resolution at startup) does not crash if the package is missing.

from .tools import (
    PROPOSAL_TOOLS,
    get_customer_ledgers as _get_customer_ledgers,
    get_project_workers as _get_project_workers,
    get_supplier_ledgers as _get_supplier_ledgers,
    propose_supplier_payment as _propose_supplier_payment,
    propose_transaction as _propose_transaction,
    propose_worker_attendance as _propose_worker_attendance,
    query_customer_balance as _query_customer_balance,
    query_project_expense_summary as _query_project_expense_summary,
    query_supplier_pending as _query_supplier_pending,
    search_customers as _search_customers,
    search_projects as _search_projects,
    search_suppliers as _search_suppliers,
    search_users as _search_users,
    search_workers as _search_workers,
)


logger = logging.getLogger(__name__)


MODEL = "gemini-2.5-flash"
MAX_ITERATIONS = 12


# ---------------------------------------------------------------------------
# Search tools
# ---------------------------------------------------------------------------
@tool
def search_customers(query: str) -> dict:
    """Search customers by name (first/last), username, phone, or email.

    Use FIRST whenever the user mentions a customer name. Returns matches
    with their IDs. Disambiguate when multiple, tell user clearly when zero.

    Args:
        query: Name, username, phone, or email fragment.
    """
    return _search_customers(query)


@tool
def search_users(query: str) -> dict:
    """Search staff Django users (people who handle payments).

    Use to resolve the 'paid_to' field for customer transactions.

    Args:
        query: Name, username, or email fragment.
    """
    return _search_users(query)


@tool
def search_suppliers(query: str) -> dict:
    """Search suppliers by shop name, contact name, or mobile.

    Use whenever the user mentions a supplier or vendor (e.g. 'Ramesh
    hardware', 'Ganpati cement').

    Args:
        query: Shop name / first name / last name / mobile fragment.
    """
    return _search_suppliers(query)


@tool
def search_workers(query: str) -> dict:
    """Search workers by name or mobile.

    Use whenever the user mentions a worker / mistri / labourer by name.

    Args:
        query: Name or mobile fragment.
    """
    return _search_workers(query)


@tool
def search_projects(query: str = "") -> dict:
    """Search projects by name or slug. Pass empty string to list all
    active/upcoming projects.

    Use whenever a project / site is mentioned, OR to ask the user which
    project an action belongs to when unclear.

    Args:
        query: Name fragment, or empty string to list all.
    """
    return _search_projects(query)


# ---------------------------------------------------------------------------
# Lookup tools
# ---------------------------------------------------------------------------
@tool
def get_customer_ledgers(customer_id: int) -> dict:
    """Get all CustomerLedgers for a customer (one per house/property).

    A customer can have multiple ledgers across different projects/houses.
    Use this to let the user pick which ledger the transaction belongs to
    when there are several.

    Args:
        customer_id: ID returned by search_customers.
    """
    return _get_customer_ledgers(customer_id)


@tool
def get_supplier_ledgers(project_id: int = 0, supplier_id: int = 0) -> dict:
    """Find ProjectSupplierLedger rows (item-level supplier records with a
    running balance). A supplier payment is made AGAINST one of these
    rows, so this is needed to resolve 'supplier_ledger_id' for
    propose_supplier_payment.

    Provide at least project_id or supplier_id (or both). Use 0 to skip.

    Args:
        project_id: Project ID to filter by, or 0 to skip.
        supplier_id: Supplier ID to filter by, or 0 to skip.
    """
    return _get_supplier_ledgers(
        project_id=project_id or None,
        supplier_id=supplier_id or None,
    )


@tool
def get_project_workers(project_id: int, worker_id: int = 0) -> dict:
    """Find ProjectWorkers - the link between a worker and a project that
    holds the agreed wages_type and wages amount. An attendance entry must
    reference one of these rows, so this is needed to resolve
    'project_worker_id' for propose_worker_attendance.

    Args:
        project_id: Project ID.
        worker_id: Worker ID to filter by, or 0 to list all.
    """
    return _get_project_workers(
        project_id=project_id,
        worker_id=worker_id or None,
    )


# ---------------------------------------------------------------------------
# Propose tools (do not save)
# ---------------------------------------------------------------------------
@tool
def propose_transaction(
    customer_ledger_id: int,
    amount: float,
    payment_type: str,
    paid_on: str,
    paid_to_user_id: int,
    detail: str,
) -> dict:
    """Propose a CustomerLedgerTransaction for the user to confirm.

    Does NOT save anything. Returns a preview that the user reviews and
    confirms via the UI. Only call when EVERY field is resolved with no
    ambiguity.

    *** CRITICAL ID WARNING ***
    customer_ledger_id is the `id` from get_customer_ledgers (the
    CustomerLedger row id). It is NOT the customer_id from
    search_customers. These are different numbers. Do NOT guess.

    Args:
        customer_ledger_id: `id` from get_customer_ledgers response.
        amount: Amount in rupees (positive number).
        payment_type: 'credited' when customer pays us OR we pay someone
            on customer's behalf - both reduce customer's outstanding
            balance. 'debited' when we refund money TO the customer.
        paid_on: Date in YYYY-MM-DD format.
        paid_to_user_id: ID of the Django User who handled the payment.
        detail: Free-text narrative preserving user's phrasing.
    """
    return _propose_transaction(
        customer_ledger_id=customer_ledger_id,
        amount=amount,
        payment_type=payment_type,
        paid_on=paid_on,
        paid_to_user_id=paid_to_user_id,
        detail=detail,
    )


@tool
def propose_supplier_payment(
    supplier_ledger_id: int,
    payment_amount: float,
    payment_date: str,
    payment_mode: str,
    reference_number: str = "",
    notes: str = "",
) -> dict:
    """Propose a ProjectSupplierPayment for the user to confirm.

    Does NOT save. Returns a preview. Use AFTER resolving the specific
    ProjectSupplierLedger row via get_supplier_ledgers (a payment is made
    against one ledger entry, not directly against a supplier).

    *** CRITICAL ID WARNING ***
    supplier_ledger_id is the `id` from get_supplier_ledgers (the
    ProjectSupplierLedger row id). It is NOT the supplier_id from
    search_suppliers. These are different numbers. Do NOT guess.

    Args:
        supplier_ledger_id: `id` from get_supplier_ledgers response.
        payment_amount: Amount paid in rupees (positive number).
        payment_date: Date in YYYY-MM-DD format.
        payment_mode: One of 'cash', 'cheque', 'online', 'bank_transfer'.
            Default to 'cash' if user does not specify.
        reference_number: Cheque/UTR/txn reference (optional).
        notes: Free-text notes (optional).
    """
    return _propose_supplier_payment(
        supplier_ledger_id=supplier_ledger_id,
        payment_amount=payment_amount,
        payment_date=payment_date,
        payment_mode=payment_mode,
        reference_number=reference_number,
        notes=notes,
    )


@tool
def propose_worker_attendance(
    project_worker_id: int,
    working_date: str,
    total_amount: float,
    paid_amount: float = 0,
) -> dict:
    """Propose a ProjectWorkerAttendances for the user to confirm.

    Does NOT save. Returns a preview. Use ONLY AFTER calling
    get_project_workers and reading the 'id' from its response.

    *** CRITICAL ID WARNING ***
    project_worker_id is the `id` returned by get_project_workers
    (the ProjectWorkers row id). It is NOT the worker_id returned by
    search_workers. These are different numbers. Mixing them up will
    fail. If get_project_workers returns count=0, the worker is not
    assigned to that project — tell the user; DO NOT guess an id and
    DO NOT call this tool.

    Compute total_amount from the worker's wages_type and the units
    reported by the user. Examples:
      - wages_type 'Per Day', wages 800, user says '1 din': total = 800
      - wages_type 'Per Hour', wages 100, user says '6 ghante': total = 600
      - wages_type 'Lum Sum': total = whatever user states
    If the user doesn't say how much was actually handed over, set
    paid_amount to 0 (just attendance recorded, no cash paid).

    Args:
        project_worker_id: `id` from get_project_workers response (NOT
            the worker_id from search_workers).
        working_date: Date in YYYY-MM-DD format.
        total_amount: Wage owed for this attendance (positive).
        paid_amount: Cash actually paid today; 0 if none.
    """
    return _propose_worker_attendance(
        project_worker_id=project_worker_id,
        working_date=working_date,
        total_amount=total_amount,
        paid_amount=paid_amount,
    )


# ---------------------------------------------------------------------------
# Read-only query tools
# ---------------------------------------------------------------------------
@tool
def query_customer_balance(customer_id: int) -> dict:
    """Look up a customer's total billed, total paid, and total outstanding
    across all of their property ledgers.

    Args:
        customer_id: ID returned by search_customers.
    """
    return _query_customer_balance(customer_id)


@tool
def query_project_expense_summary(
    project_id: int,
    from_date: str = "",
    to_date: str = "",
) -> dict:
    """Aggregate project expenses (worker payments + supplier payments +
    other) from the master ProjectLedger, optionally filtered by date range.

    Args:
        project_id: Project ID.
        from_date: Optional start date YYYY-MM-DD (inclusive).
        to_date: Optional end date YYYY-MM-DD (inclusive).
    """
    return _query_project_expense_summary(
        project_id=project_id,
        from_date=from_date,
        to_date=to_date,
    )


@tool
def query_supplier_pending(supplier_id: int = 0, project_id: int = 0) -> dict:
    """Sum outstanding balances across supplier ledgers. Filter by
    supplier and/or project (use 0 to skip a filter).

    Args:
        supplier_id: Supplier ID, or 0 for all suppliers.
        project_id: Project ID, or 0 for all projects.
    """
    return _query_supplier_pending(
        supplier_id=supplier_id or None,
        project_id=project_id or None,
    )


TOOLS = [
    search_customers,
    search_users,
    search_suppliers,
    search_workers,
    search_projects,
    get_customer_ledgers,
    get_supplier_ledgers,
    get_project_workers,
    propose_transaction,
    propose_supplier_payment,
    propose_worker_attendance,
    query_customer_balance,
    query_project_expense_summary,
    query_supplier_pending,
]


def _system_prompt() -> str:
    return (
        "You are an AI accounting assistant for SVED (Siddhi Vinayak Estate "
        "Developers), a real-estate project management system. You help the "
        "superadmin via natural-language instructions in Hindi (Romanized), "
        "English, or a mix.\n\n"
        "## What you can do\n"
        "You handle THREE kinds of write actions plus read-only questions:\n"
        "1. Customer ledger transaction (customer paid us, or we paid "
        "someone on customer's behalf, or refund TO customer)\n"
        "2. Supplier payment (we paid a supplier against an item-level "
        "supplier ledger)\n"
        "3. Worker attendance + wage (record a worker's attendance for a "
        "project, with optional wage paid that day)\n"
        "Plus read-only queries: customer balance, project expense summary, "
        "supplier pending.\n\n"
        "Decide kind by intent:\n"
        "- Mentions a CUSTOMER name + amount -> kind 1\n"
        "- Mentions a SUPPLIER / shop / vendor + amount -> kind 2\n"
        "- Mentions a WORKER / mistri / labourer + project/site -> kind 3\n"
        "- Asks 'kitna', 'pending', 'kharcha', 'balance', 'outstanding', "
        "'how much', 'summary' -> read-only query, no proposal\n"
        "If unclear, ASK the user.\n\n"
        "## General rules\n"
        "- If a search returns multiple matches, ASK to disambiguate. Show "
        "candidates as a short numbered list with a distinguishing field.\n"
        "- If a search returns ZERO matches, tell the user clearly. Do NOT "
        "invent IDs or guess.\n"
        "- Never call a propose_* tool with guessed or partial data.\n"
        "- After a propose_* tool returns ok, write a brief confirmation "
        "in the user's language saying the preview is ready for review.\n"
        "- For read-only queries, after the query tool returns, summarize "
        "the result conversationally (don't dump JSON). Use rupees with "
        "Rs. prefix.\n\n"
        "## ID handling (VERY IMPORTANT)\n"
        "Different tools return different IDs. NEVER mix them up. NEVER "
        "guess. The propose_* tools need link-table IDs from get_* tools, "
        "not entity IDs from search_* tools:\n"
        "- propose_transaction needs `customer_ledger_id` -> the `id` from "
        "get_customer_ledgers (NOT the customer_id from search_customers).\n"
        "- propose_supplier_payment needs `supplier_ledger_id` -> the `id` "
        "from get_supplier_ledgers (NOT the supplier_id from "
        "search_suppliers).\n"
        "- propose_worker_attendance needs `project_worker_id` -> the `id` "
        "from get_project_workers (NOT the worker_id from search_workers).\n"
        "If the relevant get_* tool returns count=0, the entity is not "
        "linked to that project — TELL the user and STOP. Do NOT call the "
        "propose_* tool with a guessed id like 1.\n\n"
        "## Workflow - kind 1 (customer transaction)\n"
        "Resolve: customer -> ledger (if multiple, ask) -> amount -> "
        "paid_on -> paid_to user -> payment_type -> detail. Then call "
        "propose_transaction.\n"
        "payment_type rules:\n"
        "- Customer paid us money -> 'credited'\n"
        "- We paid someone (carpenter/supplier/worker) on customer's "
        "behalf or instruction -> 'credited' (still reduces their "
        "outstanding balance)\n"
        "- We refunded money TO the customer -> 'debited'\n"
        "- If unclear, default to 'credited' and mention it.\n\n"
        "## Workflow - kind 2 (supplier payment)\n"
        "Resolve: supplier -> project -> the SPECIFIC ProjectSupplierLedger "
        "row (call get_supplier_ledgers; if multiple, ask user which item "
        "/ ledger entry the payment is against) -> payment_amount -> "
        "payment_date -> payment_mode (default 'cash' if user didn't say) "
        "-> reference_number / notes if mentioned. Then call "
        "propose_supplier_payment.\n"
        "If no supplier ledger exists yet for that supplier+project, tell "
        "the user it must be created first via the admin (a payment "
        "needs an existing item-level ledger to attach to).\n\n"
        "## Workflow - kind 3 (worker attendance)\n"
        "Steps in ORDER (do not skip):\n"
        "1. search_workers(name) -> get worker_id\n"
        "2. search_projects(name) -> get project_id\n"
        "3. get_project_workers(project_id, worker_id) -> get the `id` "
        "field from the response. THIS is the project_worker_id.\n"
        "   - If count=0, worker is not assigned to that project. Tell "
        "the user and STOP. DO NOT call propose_worker_attendance.\n"
        "4. Compute total_amount from wages_type * units the user "
        "reported. If user didn't say full day vs half day, ASK.\n"
        "5. paid_amount = 0 unless user said cash was actually handed.\n"
        "6. propose_worker_attendance(project_worker_id=<id from step 3>, "
        "...).\n\n"
        "## Off-topic queries (VERY IMPORTANT)\n"
        "If the user asks about ANYTHING outside of SVED project management "
        "(e.g. general knowledge, weather, sports, politics, coding help, "
        "other businesses, personal advice, or any topic unrelated to "
        "customers, suppliers, workers, projects, ledgers, payments, or "
        "attendance) — respond with EXACTLY this message and nothing else:\n"
        "\"Sorry, main sirf is project se related queries handle karta hoon. "
        "Please apna question relevant topic par poochiye.\"\n"
        "Do NOT use any tool. Do NOT explain. Just output that message.\n\n"
        "## Style\n"
        "- Reply in the user's language (Hindi Romanized if Hindi, English "
        "if English).\n"
        "- Be concise. No long explanations - just the question, the "
        "preview confirmation, or the answer.\n"
        "- When asking to disambiguate, use a short numbered list.\n"
        f"\n## Today's date\n{date.today().isoformat()}\n"
    )


def _build_llm():
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as e:
        raise RuntimeError(
            "langchain-google-genai is not installed. Run "
            "`pip install langchain-google-genai` to enable the AI agent."
        ) from e

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Generate one at https://aistudio.google.com/apikey "
            "and add it to your .env file."
        )
    return ChatGoogleGenerativeAI(
        model=MODEL,
        google_api_key=api_key,
        temperature=0.2,
    )


def _build_executor() -> AgentExecutor:
    llm = _build_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", _system_prompt()),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        return_intermediate_steps=True,
        max_iterations=MAX_ITERATIONS,
        verbose=False,
        handle_parsing_errors=True,
    )


def _extract_proposal(intermediate_steps) -> Optional[Dict]:
    """Find the latest successful propose_* call and return its preview
    (with `kind` baked in)."""
    proposal = None
    for action, observation in intermediate_steps:
        tool_name = getattr(action, "tool", None)
        if tool_name not in PROPOSAL_TOOLS:
            continue

        if isinstance(observation, dict):
            parsed = observation
        elif isinstance(observation, str):
            try:
                parsed = json.loads(observation)
            except (json.JSONDecodeError, TypeError):
                continue
        else:
            continue

        if parsed.get("ok") and parsed.get("preview"):
            preview = dict(parsed["preview"])
            # Make sure kind is on the preview itself for downstream consumers.
            preview.setdefault("kind", parsed.get("kind") or _kind_from_tool(tool_name))
            proposal = preview
    return proposal


def _kind_from_tool(tool_name: str) -> str:
    return {
        "propose_transaction": "customer_txn",
        "propose_supplier_payment": "supplier_payment",
        "propose_worker_attendance": "worker_attendance",
    }.get(tool_name, "customer_txn")


def run_turn(history_messages: List[Dict], user_input: str) -> Dict:
    """Run one user turn through the LangChain agent.

    Returns:
        dict with keys:
            - assistant_text: final text response shown to the user
            - proposal: preview dict (with `kind`) or None
    """
    chat_history = []
    for m in history_messages:
        content = m.get("content")
        if not isinstance(content, str) or not content:
            continue
        if m.get("role") == "user":
            chat_history.append(HumanMessage(content=content))
        elif m.get("role") == "assistant":
            chat_history.append(AIMessage(content=content))

    executor = _build_executor()
    result = executor.invoke({
        "input": user_input,
        "chat_history": chat_history,
    })

    final_text = result.get("output") or ""
    if not isinstance(final_text, str):
        try:
            final_text = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p)
                for p in final_text
            )
        except Exception:
            final_text = str(final_text)

    proposal = _extract_proposal(result.get("intermediate_steps", []))

    return {
        "assistant_text": final_text.strip(),
        "proposal": proposal,
    }
