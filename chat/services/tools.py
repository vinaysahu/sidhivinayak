"""
Tool implementations exposed to the LangChain AI agent.

The agent calls these to look up entities (customers, ledgers, suppliers,
workers, projects, staff users) and to propose write operations:

  - propose_transaction          -> CustomerLedgerTransaction
  - propose_supplier_payment     -> ProjectSupplierPayment
  - propose_worker_attendance    -> ProjectWorkerAttendances

The propose_* tools do NOT save anything to the database. They return a
preview payload that the caller (views.py) persists as a PendingTransaction
and shows to the user for confirmation.

It also exposes read-only query tools used to answer questions:

  - query_customer_balance
  - query_project_expense_summary
  - query_supplier_pending
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.db.models import Q, Sum

from customers.models.Customers import Customers
from customers.models.CustomerLedger import CustomerLedger
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from customers.models.CustomerEnquiry import CustomerEnquiry
from customers.models.PropertySellRequest import PropertySellRequest
from globals.models.Suppliers import Suppliers
from projects.models.Projects import Projects
from projects.models.ProjectHouses import ProjectHouses
from projects.models.ProjectLedger import ProjectLedger
from projects.models.ProjectMaterials import ProjectMaterials
from projects.models.ProjectSupplierLedger import ProjectSupplierLedger
from projects.models.ProjectWorkers import ProjectWorkers
from projects.models.ProjectWorkerAttendances import ProjectWorkerAttendances
from accounts.models.UserLedger import UserLedger
from workers.models.Workers import Workers


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
def _customer_to_dict(c: Customers) -> dict:
    full_name = " ".join(filter(None, [c.first_name, c.last_name])).strip()
    return {
        "id": c.id,
        "username": c.username,
        "full_name": full_name or c.username,
        "phone_no": c.phone_no or "",
        "email": c.email,
    }


def _user_to_dict(u: User) -> dict:
    full_name = " ".join(filter(None, [u.first_name, u.last_name])).strip()
    return {
        "id": u.id,
        "username": u.username,
        "full_name": full_name or u.username,
        "email": u.email or "",
    }


def _supplier_to_dict(s: Suppliers) -> dict:
    contact = " ".join(filter(None, [s.first_name, s.last_name])).strip()
    return {
        "id": s.id,
        "shop_name": s.shop_name,
        "contact_name": contact,
        "mobile": s.mobile or "",
    }


def _worker_to_dict(w: Workers) -> dict:
    return {
        "id": w.id,
        "name": w.name,
        "mobile": w.mobile or "",
        "worker_type": str(w.worker_type_id) if w.worker_type_id_id else "",
        "default_wages": w.wages,
        "default_wages_type": w.get_wages_type_display(),
    }


def _project_to_dict(p: Projects) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "status": p.get_status_display(),
    }


# ---------------------------------------------------------------------------
# Search tools
# ---------------------------------------------------------------------------
def search_customers(query: str) -> dict:
    q = (query or "").strip()
    if not q:
        return {"results": [], "note": "Empty query"}

    qs = Customers.objects.filter(
        Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(username__icontains=q)
        | Q(phone_no__icontains=q)
        | Q(email__icontains=q),
        status=Customers.STATUS_ACTIVE,
    ).order_by("first_name", "last_name")[:20]

    results = [_customer_to_dict(c) for c in qs]
    return {"count": len(results), "results": results}


def search_users(query: str) -> dict:
    q = (query or "").strip()
    if not q:
        return {"results": [], "note": "Empty query"}

    qs = User.objects.filter(
        Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(username__icontains=q)
        | Q(email__icontains=q),
        is_active=True,
    ).order_by("first_name", "last_name")[:20]

    results = [_user_to_dict(u) for u in qs]
    return {"count": len(results), "results": results}


def search_suppliers(query: str) -> dict:
    q = (query or "").strip()
    if not q:
        return {"results": [], "note": "Empty query"}

    qs = Suppliers.objects.filter(
        Q(shop_name__icontains=q)
        | Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(mobile__icontains=q),
        status=10,
    ).order_by("shop_name")[:20]

    results = [_supplier_to_dict(s) for s in qs]
    return {"count": len(results), "results": results}


def search_workers(query: str) -> dict:
    q = (query or "").strip()
    if not q:
        return {"results": [], "note": "Empty query"}

    qs = Workers.objects.filter(
        Q(name__icontains=q) | Q(mobile__icontains=q),
        status=Workers.STATUS_ACTIVE,
    ).order_by("name")[:20]

    results = [_worker_to_dict(w) for w in qs]
    return {"count": len(results), "results": results}


def search_projects(query: str) -> dict:
    q = (query or "").strip()
    qs = Projects.objects.exclude(status=Projects.STATUS_DELETED)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    qs = qs.order_by("name")[:20]
    results = [_project_to_dict(p) for p in qs]
    return {"count": len(results), "results": results}


# ---------------------------------------------------------------------------
# Lookup tools
# ---------------------------------------------------------------------------
def get_customer_ledgers(customer_id: int) -> dict:
    try:
        customer = Customers.objects.get(id=customer_id)
    except Customers.DoesNotExist:
        return {"error": f"Customer {customer_id} not found"}

    ledgers = (
        CustomerLedger.objects.filter(customer_id=customer)
        .select_related("project_id", "project_house_id")
    )

    results = []
    for l in ledgers:
        results.append({
            "id": l.id,
            "project": str(l.project_id),
            "project_id": l.project_id_id,
            "house": str(l.project_house_id),
            "house_id": l.project_house_id_id,
            "total_amount": str(l.amount),
            "outstanding_balance": str(l.balance),
        })

    return {
        "customer": _customer_to_dict(customer),
        "ledger_count": len(results),
        "ledgers": results,
    }


def get_supplier_ledgers(project_id: int = None, supplier_id: int = None) -> dict:
    """
    Find ProjectSupplierLedger rows. A supplier ledger is a record of items
    received by a project from a supplier with a running balance. Payments
    are made against a specific ledger entry.

    At least one of project_id or supplier_id must be given.
    """
    if not project_id and not supplier_id:
        return {"error": "Provide at least project_id or supplier_id"}

    qs = ProjectSupplierLedger.objects.select_related("project", "supplier")
    if project_id:
        qs = qs.filter(project_id=project_id)
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    qs = qs.order_by("-item_date")[:30]

    results = []
    for l in qs:
        results.append({
            "id": l.id,
            "project": str(l.project),
            "project_id": l.project_id,
            "supplier": l.supplier.shop_name,
            "supplier_id": l.supplier_id,
            "item_description": l.item_description,
            "item_date": l.item_date.isoformat(),
            "total_amount": str(l.total_amount),
            "paid_amount": str(l.paid_amount),
            "balance": str(l.balance),
        })

    return {"count": len(results), "ledgers": results}


def get_project_workers(project_id: int, worker_id: int = None) -> dict:
    """
    Find ProjectWorkers - the link between a worker and a project that
    holds the agreed wages_type and wages amount. Attendance entries
    reference this row, so it must exist before an attendance can be
    proposed.
    """
    qs = ProjectWorkers.objects.filter(
        project_id=project_id,
        status=ProjectWorkers.STATUS_ACTIVE,
    ).select_related("project_id", "worker_id")
    if worker_id:
        qs = qs.filter(worker_id=worker_id)
    qs = qs.order_by("worker_id__name")[:30]

    results = []
    for pw in qs:
        results.append({
            "id": pw.id,
            "project": str(pw.project_id),
            "project_id": pw.project_id_id,
            "worker": pw.worker_id.name,
            "worker_id": pw.worker_id_id,
            "wages_type": pw.get_wages_type_display(),
            "wages_type_code": pw.wages_type,
            "wages": pw.wages,
        })

    if not results:
        if worker_id:
            note = (
                f"No ProjectWorkers row found linking worker_id={worker_id} "
                f"to project_id={project_id}. The worker is NOT assigned to "
                f"this project. Tell the user this clearly. DO NOT call "
                f"propose_worker_attendance with a guessed project_worker_id."
            )
        else:
            note = (
                f"No active workers assigned to project_id={project_id}. "
                f"Tell the user. DO NOT guess an id."
            )
        return {"count": 0, "project_workers": [], "note": note}

    return {"count": len(results), "project_workers": results}


# ---------------------------------------------------------------------------
# Propose tools (do not save)
# ---------------------------------------------------------------------------
def propose_transaction(
    customer_ledger_id: int,
    amount,
    payment_type: str,
    paid_on: str,
    paid_to_user_id: int,
    detail: str,
) -> dict:
    """Propose a CustomerLedgerTransaction preview."""
    errors = []

    try:
        ledger = (
            CustomerLedger.objects
            .select_related("customer_id", "project_id", "project_house_id")
            .get(id=customer_ledger_id)
        )
    except CustomerLedger.DoesNotExist:
        return {
            "error": (
                f"CustomerLedger id={customer_ledger_id} does not exist. "
                f"You must call get_customer_ledgers(customer_id) FIRST "
                f"and use the 'id' field from its response — that is the "
                f"customer_ledger_id. Do NOT pass the customer_id from "
                f"search_customers. Do NOT guess."
            )
        }

    try:
        paid_to = User.objects.get(id=paid_to_user_id)
    except User.DoesNotExist:
        return {"error": f"User {paid_to_user_id} does not exist"}

    try:
        amount_dec = Decimal(str(amount))
        if amount_dec <= 0:
            errors.append("amount must be positive")
    except (InvalidOperation, TypeError):
        errors.append(f"amount '{amount}' is not a valid number")
        amount_dec = None

    if payment_type not in ("credited", "debited"):
        errors.append(f"payment_type must be 'credited' or 'debited', got '{payment_type}'")

    try:
        paid_on_date = date.fromisoformat(paid_on)
    except (TypeError, ValueError):
        errors.append(f"paid_on '{paid_on}' is not a valid YYYY-MM-DD date")
        paid_on_date = None

    if errors:
        return {"error": "; ".join(errors)}

    customer = ledger.customer_id
    customer_name = " ".join(filter(None, [customer.first_name, customer.last_name])).strip() or customer.username
    paid_to_name = " ".join(filter(None, [paid_to.first_name, paid_to.last_name])).strip() or paid_to.username

    return {
        "ok": True,
        "kind": "customer_txn",
        "preview": {
            "kind": "customer_txn",
            "customer_ledger_id": ledger.id,
            "customer_name": customer_name,
            "project": str(ledger.project_id),
            "house": str(ledger.project_house_id),
            "amount": str(amount_dec),
            "payment_type": payment_type,
            "paid_on": paid_on_date.isoformat(),
            "paid_to_user_id": paid_to.id,
            "paid_to_name": paid_to_name,
            "detail": detail,
        },
    }


def propose_supplier_payment(
    supplier_ledger_id: int,
    payment_amount,
    payment_date: str,
    payment_mode: str,
    reference_number: str = "",
    notes: str = "",
) -> dict:
    """Propose a ProjectSupplierPayment preview."""
    errors = []

    try:
        sl = (
            ProjectSupplierLedger.objects
            .select_related("project", "supplier")
            .get(id=supplier_ledger_id)
        )
    except ProjectSupplierLedger.DoesNotExist:
        return {
            "error": (
                f"ProjectSupplierLedger id={supplier_ledger_id} does not "
                f"exist. You must call get_supplier_ledgers(project_id, "
                f"supplier_id) FIRST and use the 'id' field from its "
                f"response — that is the supplier_ledger_id. Do NOT pass "
                f"the supplier_id from search_suppliers. Do NOT guess."
            )
        }

    try:
        amount_dec = Decimal(str(payment_amount))
        if amount_dec <= 0:
            errors.append("payment_amount must be positive")
    except (InvalidOperation, TypeError):
        errors.append(f"payment_amount '{payment_amount}' is not a valid number")
        amount_dec = None

    valid_modes = {"cash", "cheque", "online", "bank_transfer"}
    if payment_mode not in valid_modes:
        errors.append(f"payment_mode must be one of {sorted(valid_modes)}, got '{payment_mode}'")

    try:
        payment_dt = date.fromisoformat(payment_date)
    except (TypeError, ValueError):
        errors.append(f"payment_date '{payment_date}' is not a valid YYYY-MM-DD date")
        payment_dt = None

    if errors:
        return {"error": "; ".join(errors)}

    return {
        "ok": True,
        "kind": "supplier_payment",
        "preview": {
            "kind": "supplier_payment",
            "supplier_ledger_id": sl.id,
            "supplier": sl.supplier.shop_name,
            "supplier_id": sl.supplier_id,
            "project": str(sl.project),
            "project_id": sl.project_id,
            "item_description": sl.item_description,
            "ledger_total": str(sl.total_amount),
            "ledger_paid": str(sl.paid_amount),
            "ledger_balance": str(sl.balance),
            "payment_amount": str(amount_dec),
            "payment_date": payment_dt.isoformat(),
            "payment_mode": payment_mode,
            "reference_number": reference_number or "",
            "notes": notes or "",
        },
    }


def propose_worker_attendance(
    project_worker_id: int,
    working_date: str,
    total_amount,
    paid_amount=None,
) -> dict:
    """Propose a ProjectWorkerAttendances preview.

    If paid_amount is None it defaults to 0 (attendance recorded but no
    cash paid yet). The signal layer will create a ProjectLedger entry
    only when paid_amount > 0.
    """
    errors = []

    try:
        pw = (
            ProjectWorkers.objects
            .select_related("project_id", "worker_id")
            .get(id=project_worker_id)
        )
    except ProjectWorkers.DoesNotExist:
        return {
            "error": (
                f"ProjectWorkers id={project_worker_id} does not exist. "
                f"You must call get_project_workers(project_id, worker_id) "
                f"FIRST and use the 'id' field from its response — that is "
                f"the project_worker_id. Do NOT pass the worker_id from "
                f"search_workers. Do NOT guess. If get_project_workers "
                f"returns count=0, the worker is not assigned to that "
                f"project — tell the user instead of calling this tool."
            )
        }

    try:
        total_dec = Decimal(str(total_amount))
        if total_dec < 0:
            errors.append("total_amount cannot be negative")
    except (InvalidOperation, TypeError):
        errors.append(f"total_amount '{total_amount}' is not a valid number")
        total_dec = None

    if paid_amount is None or paid_amount == "":
        paid_dec = Decimal("0")
    else:
        try:
            paid_dec = Decimal(str(paid_amount))
            if paid_dec < 0:
                errors.append("paid_amount cannot be negative")
        except (InvalidOperation, TypeError):
            errors.append(f"paid_amount '{paid_amount}' is not a valid number")
            paid_dec = None

    if total_dec is not None and paid_dec is not None and paid_dec > total_dec:
        errors.append("paid_amount cannot exceed total_amount")

    try:
        working_dt = date.fromisoformat(working_date)
    except (TypeError, ValueError):
        errors.append(f"working_date '{working_date}' is not a valid YYYY-MM-DD date")
        working_dt = None

    if errors:
        return {"error": "; ".join(errors)}

    remaining = total_dec - paid_dec

    return {
        "ok": True,
        "kind": "worker_attendance",
        "preview": {
            "kind": "worker_attendance",
            "project_worker_id": pw.id,
            "project": str(pw.project_id),
            "project_id": pw.project_id_id,
            "worker": pw.worker_id.name,
            "worker_id": pw.worker_id_id,
            "wages_type": pw.get_wages_type_display(),
            "wages": pw.wages,
            "working_date": working_dt.isoformat(),
            "total_amount": str(total_dec),
            "paid_amount": str(paid_dec),
            "remaining_amount": str(remaining),
        },
    }


# ---------------------------------------------------------------------------
# Read-only query tools
# ---------------------------------------------------------------------------
def query_customer_balance(customer_id: int) -> dict:
    """Return total billed, paid, and outstanding amounts across all of a
    customer's ledgers (one per house)."""
    try:
        customer = Customers.objects.get(id=customer_id)
    except Customers.DoesNotExist:
        return {"error": f"Customer {customer_id} not found"}

    ledgers = (
        CustomerLedger.objects.filter(customer_id=customer)
        .select_related("project_id", "project_house_id")
    )

    total = Decimal("0")
    outstanding = Decimal("0")
    per_ledger = []
    for l in ledgers:
        total += l.amount or Decimal("0")
        outstanding += l.balance or Decimal("0")
        per_ledger.append({
            "ledger_id": l.id,
            "project": str(l.project_id),
            "house": str(l.project_house_id),
            "total_amount": str(l.amount),
            "outstanding_balance": str(l.balance),
        })

    return {
        "customer": _customer_to_dict(customer),
        "total_billed": str(total),
        "total_outstanding": str(outstanding),
        "total_paid": str(total - outstanding),
        "ledgers": per_ledger,
    }


def query_project_expense_summary(
    project_id: int,
    from_date: str = "",
    to_date: str = "",
) -> dict:
    """Aggregate ProjectLedger expenses for a project, optionally within a
    date range. Returns totals broken down by entry_type plus a grand total."""
    try:
        project = Projects.objects.get(id=project_id)
    except Projects.DoesNotExist:
        return {"error": f"Project {project_id} not found"}

    qs = ProjectLedger.objects.filter(project=project)

    if from_date:
        try:
            qs = qs.filter(entry_date__gte=date.fromisoformat(from_date))
        except ValueError:
            return {"error": f"from_date '{from_date}' is not valid YYYY-MM-DD"}
    if to_date:
        try:
            qs = qs.filter(entry_date__lte=date.fromisoformat(to_date))
        except ValueError:
            return {"error": f"to_date '{to_date}' is not valid YYYY-MM-DD"}

    by_type = {}
    for entry_type, label in ProjectLedger.ENTRY_TYPE_CHOICES:
        agg = qs.filter(entry_type=entry_type).aggregate(total=Sum("amount"))
        by_type[entry_type] = {
            "label": label,
            "total": str(agg["total"] or Decimal("0")),
        }

    grand = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return {
        "project": str(project),
        "project_id": project.id,
        "from_date": from_date or None,
        "to_date": to_date or None,
        "by_entry_type": by_type,
        "grand_total": str(grand),
        "entry_count": qs.count(),
    }


def query_supplier_pending(supplier_id: int = None, project_id: int = None) -> dict:
    """Sum outstanding balances across ProjectSupplierLedger rows. Filter
    by supplier_id and/or project_id. Returns per-ledger detail plus totals."""
    qs = ProjectSupplierLedger.objects.select_related("project", "supplier")
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    if project_id:
        qs = qs.filter(project_id=project_id)

    if not qs.exists():
        return {
            "count": 0,
            "ledgers": [],
            "total_billed": "0",
            "total_paid": "0",
            "total_pending": "0",
        }

    ledgers = []
    total_billed = Decimal("0")
    total_paid = Decimal("0")
    total_pending = Decimal("0")
    for l in qs.order_by("-item_date")[:50]:
        total_billed += l.total_amount or Decimal("0")
        total_paid += l.paid_amount or Decimal("0")
        total_pending += l.balance or Decimal("0")
        ledgers.append({
            "ledger_id": l.id,
            "supplier": l.supplier.shop_name,
            "project": str(l.project),
            "item_description": l.item_description,
            "item_date": l.item_date.isoformat(),
            "total_amount": str(l.total_amount),
            "paid_amount": str(l.paid_amount),
            "balance": str(l.balance),
        })

    return {
        "count": len(ledgers),
        "ledgers": ledgers,
        "total_billed": str(total_billed),
        "total_paid": str(total_paid),
        "total_pending": str(total_pending),
    }


# ---------------------------------------------------------------------------
# Extended read-only query tools
# ---------------------------------------------------------------------------

def query_project_houses(project_id: int, status_filter: str = "") -> dict:
    """List all houses in a project with their status, assigned customer, price,
    and completion percentage.

    status_filter values: 'available', 'agreement', 'sold', 'hold', or '' for all.
    """
    try:
        project = Projects.objects.get(id=project_id)
    except Projects.DoesNotExist:
        return {"error": f"Project {project_id} not found"}

    STATUS_MAP = {
        "available": 10,
        "agreement": 20,
        "sold": 30,
        "hold": 40,
    }

    qs = ProjectHouses.objects.filter(project_id=project).select_related("customer_id")
    if status_filter:
        code = STATUS_MAP.get(status_filter.lower())
        if code:
            qs = qs.filter(status=code)

    qs = qs.order_by("plot_no")

    rows = []
    counts = {"available": 0, "agreement": 0, "sold": 0, "hold": 0}
    for h in qs:
        customer_name = ""
        if h.customer_id:
            customer_name = (
                f"{h.customer_id.first_name or ''} {h.customer_id.last_name or ''}".strip()
                or h.customer_id.username
            )
        status_label = h.get_status_display()
        for k, v in STATUS_MAP.items():
            if h.status == v:
                counts[k] += 1
        rows.append({
            "plot_no": h.plot_no,
            "status": status_label,
            "customer_name": customer_name or "—",
            "price": str(h.price or ""),
            "area_sqyd": str(h.area_sqyd or ""),
            "complete_percentage": h.complete_percentage,
        })

    return {
        "project": str(project),
        "project_id": project.id,
        "total_houses": len(rows),
        "status_counts": counts,
        "houses": rows,
    }


def query_worker_attendance(
    project_id: int = None,
    worker_id: int = None,
    from_date: str = "",
    to_date: str = "",
) -> dict:
    """Fetch worker attendance records for a project and/or worker with
    wage totals (total earned, paid, remaining).

    At least one of project_id or worker_id must be provided.
    from_date / to_date: optional YYYY-MM-DD filters on working_date.
    """
    if not project_id and not worker_id:
        return {"error": "Provide at least project_id or worker_id"}

    qs = (
        ProjectWorkerAttendances.objects
        .select_related("project_id", "worker_id")
    )
    if project_id:
        qs = qs.filter(project_id=project_id)
    if worker_id:
        qs = qs.filter(worker_id=worker_id)
    if from_date:
        try:
            qs = qs.filter(working_date__gte=date.fromisoformat(from_date))
        except ValueError:
            return {"error": f"from_date '{from_date}' is not valid YYYY-MM-DD"}
    if to_date:
        try:
            qs = qs.filter(working_date__lte=date.fromisoformat(to_date))
        except ValueError:
            return {"error": f"to_date '{to_date}' is not valid YYYY-MM-DD"}

    qs = qs.order_by("-working_date")[:60]

    rows = []
    total_earned = Decimal("0")
    total_paid = Decimal("0")
    total_remaining = Decimal("0")

    for a in qs:
        earned = a.total_amount or Decimal("0")
        paid = a.paid_amount or Decimal("0")
        remaining = a.remaining_amount or Decimal("0")
        total_earned += earned
        total_paid += paid
        total_remaining += remaining
        rows.append({
            "worker": a.worker_id.name if a.worker_id else "—",
            "project": str(a.project_id) if a.project_id else "—",
            "working_date": a.working_date.isoformat() if a.working_date else "",
            "total_amount": str(earned),
            "paid_amount": str(paid),
            "remaining_amount": str(remaining),
        })

    return {
        "count": len(rows),
        "total_earned": str(total_earned),
        "total_paid": str(total_paid),
        "total_remaining": str(total_remaining),
        "records": rows,
    }


def query_project_materials(
    project_id: int,
    from_date: str = "",
    to_date: str = "",
) -> dict:
    """List material purchase bills for a project with supplier, amount,
    payment status, and item breakdown.

    from_date / to_date: optional YYYY-MM-DD filters on bill_date.
    """
    try:
        project = Projects.objects.get(id=project_id)
    except Projects.DoesNotExist:
        return {"error": f"Project {project_id} not found"}

    qs = (
        ProjectMaterials.objects
        .filter(project_id=project)
        .select_related("supplier_id")
        .prefetch_related("project_material_id")
    )
    if from_date:
        try:
            qs = qs.filter(bill_date__gte=date.fromisoformat(from_date))
        except ValueError:
            return {"error": f"from_date '{from_date}' is not valid YYYY-MM-DD"}
    if to_date:
        try:
            qs = qs.filter(bill_date__lte=date.fromisoformat(to_date))
        except ValueError:
            return {"error": f"to_date '{to_date}' is not valid YYYY-MM-DD"}

    qs = qs.order_by("-bill_date")[:40]

    PAYMENT_STATUS = {10: "Pending", 20: "Partial", 30: "Paid"}
    rows = []
    grand_total = Decimal("0")
    grand_paid = Decimal("0")
    grand_balance = Decimal("0")

    for m in qs:
        total = m.total_amount or Decimal("0")
        paid = m.paid_amount or Decimal("0")
        bal = m.balance or Decimal("0")
        grand_total += total
        grand_paid += paid
        grand_balance += bal

        items = []
        for li in m.project_material_id.all():
            items.append({
                "material": str(li.material_id),
                "quantity": str(li.quantity),
                "unit": li.unit or "",
                "rate": str(li.rate or ""),
                "amount": str(li.amount),
            })

        rows.append({
            "id": m.id,
            "supplier": m.supplier_id.shop_name if m.supplier_id else "—",
            "bill_no": m.bill_no or "",
            "bill_date": m.bill_date.isoformat() if m.bill_date else "",
            "total_amount": str(total),
            "paid_amount": str(paid),
            "balance": str(bal),
            "payment_status": PAYMENT_STATUS.get(m.payment_status, "—"),
            "items": items,
        })

    return {
        "project": str(project),
        "project_id": project.id,
        "bill_count": len(rows),
        "grand_total": str(grand_total),
        "grand_paid": str(grand_paid),
        "grand_balance": str(grand_balance),
        "bills": rows,
    }


def query_customer_enquiries(
    status_filter: str = "",
    project_id: int = None,
    limit: int = 20,
) -> dict:
    """List customer enquiries / leads.

    status_filter: 'new', 'contacted', 'interested', 'not_interested',
                   'converted', or '' for all.
    project_id: optional filter by project.
    limit: max rows (default 20).
    """
    STATUS_MAP = {
        "new": 10,
        "contacted": 20,
        "interested": 30,
        "not_interested": 40,
        "converted": 500,
    }
    qs = CustomerEnquiry.objects.select_related("project_id", "created_by").order_by("-created_at")
    if status_filter:
        code = STATUS_MAP.get(status_filter.lower())
        if code:
            qs = qs.filter(status=code)
    if project_id:
        qs = qs.filter(project_id=project_id)
    qs = qs[:max(1, min(limit, 50))]

    rows = []
    for e in qs:
        rows.append({
            "id": e.id,
            "name": e.name,
            "phone_no": e.phone_no,
            "email": e.email or "",
            "requirement": e.requirement,
            "property_type": e.property_type,
            "budget_min": str(e.budget_min or ""),
            "budget_max": str(e.budget_max or ""),
            "preferred_location": e.preferred_location or "",
            "status": e.get_status_display(),
            "follow_up_date": e.follow_up_date.isoformat() if e.follow_up_date else "",
            "project": str(e.project_id) if e.project_id else "—",
            "notes": e.notes or "",
            "created_at": e.created_at.isoformat() if e.created_at else "",
        })

    return {"count": len(rows), "enquiries": rows}


def query_property_sell_requests(
    status_filter: str = "",
    limit: int = 20,
) -> dict:
    """List property sell requests from owners wanting to sell via SVED.

    status_filter: 'new_lead', 'contacted', 'site_visit', 'deal_closed',
                   'rejected', or '' for all.
    """
    STATUS_MAP = {
        "new_lead": 10,
        "contacted": 20,
        "site_visit": 30,
        "deal_closed": 40,
        "rejected": 50,
    }
    qs = PropertySellRequest.objects.order_by("-created_at")
    if status_filter:
        code = STATUS_MAP.get(status_filter.lower())
        if code:
            qs = qs.filter(status=code)
    qs = qs[:max(1, min(limit, 50))]

    PROP_TYPE = {10: "Flat", 20: "House", 30: "Plot"}
    rows = []
    for r in qs:
        rows.append({
            "id": r.id,
            "owner_name": r.owner_name,
            "phone_no": r.phone_no,
            "property_type": PROP_TYPE.get(r.property_type, "—"),
            "address": r.address or "",
            "area_sqyd": str(r.area_sqyd or ""),
            "expected_price": str(r.expected_price or ""),
            "reason_for_selling": r.reason_for_selling or "",
            "status": r.get_status_display(),
            "notes": r.notes or "",
            "created_at": r.created_at.isoformat() if r.created_at else "",
        })

    return {"count": len(rows), "requests": rows}


def query_user_ledger(
    user_id: int = None,
    project_id: int = None,
) -> dict:
    """List UserLedger entries showing creditor↔debtor relationships between
    staff users, with their running balances.

    user_id: filter where the user is creditor or debtor.
    project_id: filter by project.
    At least one filter should be provided for focused results.
    """
    qs = UserLedger.objects.select_related("creditor", "debtor", "project_id")
    if user_id:
        qs = qs.filter(Q(creditor_id=user_id) | Q(debtor_id=user_id))
    if project_id:
        qs = qs.filter(project_id=project_id)
    qs = qs.order_by("-created_at")[:30]

    rows = []
    total_amount = Decimal("0")
    total_balance = Decimal("0")

    for ul in qs:
        creditor_name = (
            f"{ul.creditor.first_name or ''} {ul.creditor.last_name or ''}".strip()
            or ul.creditor.username
        )
        debtor_name = (
            f"{ul.debtor.first_name or ''} {ul.debtor.last_name or ''}".strip()
            or ul.debtor.username
        )
        amt = ul.amount or Decimal("0")
        bal = ul.balance or Decimal("0")
        total_amount += amt
        total_balance += bal
        rows.append({
            "id": ul.id,
            "creditor": creditor_name,
            "creditor_id": ul.creditor_id,
            "debtor": debtor_name,
            "debtor_id": ul.debtor_id,
            "project": str(ul.project_id) if ul.project_id else "—",
            "project_id": ul.project_id_id,
            "total_amount": str(amt),
            "balance": str(bal),
        })

    return {
        "count": len(rows),
        "total_amount": str(total_amount),
        "total_balance": str(total_balance),
        "ledgers": rows,
    }


def query_project_summary(project_id: int) -> dict:
    """Return a comprehensive overview of a project: basic info, house counts
    by status, customer revenue summary, worker wage totals, material spend,
    and supplier outstanding dues.
    """
    try:
        project = Projects.objects.get(id=project_id)
    except Projects.DoesNotExist:
        return {"error": f"Project {project_id} not found"}

    # Houses
    house_qs = ProjectHouses.objects.filter(project_id=project)
    house_totals = {
        "total": house_qs.count(),
        "available": house_qs.filter(status=10).count(),
        "agreement": house_qs.filter(status=20).count(),
        "sold": house_qs.filter(status=30).count(),
        "hold": house_qs.filter(status=40).count(),
    }

    # Customer revenue
    from customers.models.CustomerLedger import CustomerLedger as CL
    cl_agg = CL.objects.filter(project_id=project).aggregate(
        total_billed=Sum("amount"),
        total_balance=Sum("balance"),
    )
    total_billed = cl_agg["total_billed"] or Decimal("0")
    total_balance = cl_agg["total_balance"] or Decimal("0")
    customer_revenue = {
        "total_billed": str(total_billed),
        "total_collected": str(total_billed - total_balance),
        "total_outstanding": str(total_balance),
        "customer_count": CL.objects.filter(project_id=project).values("customer_id").distinct().count(),
    }

    # Worker wages
    worker_agg = ProjectWorkerAttendances.objects.filter(project_id=project).aggregate(
        total_earned=Sum("total_amount"),
        total_paid=Sum("paid_amount"),
        total_remaining=Sum("remaining_amount"),
    )
    worker_wages = {
        "total_earned": str(worker_agg["total_earned"] or Decimal("0")),
        "total_paid": str(worker_agg["total_paid"] or Decimal("0")),
        "total_remaining": str(worker_agg["total_remaining"] or Decimal("0")),
        "attendance_count": ProjectWorkerAttendances.objects.filter(project_id=project).count(),
    }

    # Material spend
    mat_agg = ProjectMaterials.objects.filter(project_id=project).aggregate(
        total=Sum("total_amount"),
        paid=Sum("paid_amount"),
        balance=Sum("balance"),
    )
    materials = {
        "total_bills": ProjectMaterials.objects.filter(project_id=project).count(),
        "total_amount": str(mat_agg["total"] or Decimal("0")),
        "paid_amount": str(mat_agg["paid"] or Decimal("0")),
        "balance": str(mat_agg["balance"] or Decimal("0")),
    }

    # Supplier dues
    sup_agg = ProjectSupplierLedger.objects.filter(project=project).aggregate(
        total=Sum("total_amount"),
        paid=Sum("paid_amount"),
        pending=Sum("balance"),
    )
    supplier_dues = {
        "total_billed": str(sup_agg["total"] or Decimal("0")),
        "total_paid": str(sup_agg["paid"] or Decimal("0")),
        "total_pending": str(sup_agg["pending"] or Decimal("0")),
    }

    # ProjectLedger grand total
    pl_agg = ProjectLedger.objects.filter(project=project).aggregate(total=Sum("amount"))
    project_ledger_total = str(pl_agg["total"] or Decimal("0"))

    return {
        "project": str(project),
        "project_id": project.id,
        "status": project.get_status_display(),
        "project_type": project.get_project_type_display(),
        "area_sqyd": str(project.area_sqyd or ""),
        "houses": house_totals,
        "customer_revenue": customer_revenue,
        "worker_wages": worker_wages,
        "materials": materials,
        "supplier_dues": supplier_dues,
        "project_ledger_total_expense": project_ledger_total,
    }


def query_all_customers_balance(
    project_id: int = None,
    only_outstanding: bool = False,
) -> dict:
    """List ALL customers with their total billed, paid, and outstanding
    balance across their property ledgers.

    Use when user asks for all customers' balances, sabhi customers ka
    balance, everyone's outstanding, kitna baaki hai sab ka, etc.

    project_id: optional — restrict to customers in one project.
    only_outstanding: if True, return only customers who still have a
                      balance > 0 (baaki hai).
    """
    qs = (
        CustomerLedger.objects
        .select_related("customer_id", "project_id", "project_house_id")
        .order_by("customer_id__first_name", "customer_id__last_name")
    )
    if project_id:
        qs = qs.filter(project_id=project_id)

    customer_map: dict = {}
    for cl in qs:
        cid = cl.customer_id_id
        if cid not in customer_map:
            c = cl.customer_id
            customer_map[cid] = {
                "customer_id": cid,
                "name": (
                    f"{c.first_name or ''} {c.last_name or ''}".strip()
                    or c.username
                ),
                "phone": c.phone_no or "",
                "total_billed": Decimal("0"),
                "total_outstanding": Decimal("0"),
                "ledgers": [],
            }
        entry = customer_map[cid]
        amount = cl.amount or Decimal("0")
        balance = cl.balance or Decimal("0")
        entry["total_billed"] += amount
        entry["total_outstanding"] += balance
        entry["ledgers"].append({
            "ledger_id": cl.id,
            "project": str(cl.project_id),
            "house": str(cl.project_house_id),
            "billed": str(amount),
            "outstanding": str(balance),
        })

    rows = []
    grand_billed = Decimal("0")
    grand_outstanding = Decimal("0")
    for entry in customer_map.values():
        paid = entry["total_billed"] - entry["total_outstanding"]
        if only_outstanding and entry["total_outstanding"] <= 0:
            continue
        grand_billed += entry["total_billed"]
        grand_outstanding += entry["total_outstanding"]
        rows.append({
            "customer_id": entry["customer_id"],
            "name": entry["name"],
            "phone": entry["phone"],
            "total_billed": str(entry["total_billed"]),
            "total_paid": str(paid),
            "total_outstanding": str(entry["total_outstanding"]),
            "ledgers": entry["ledgers"],
        })

    return {
        "count": len(rows),
        "grand_billed": str(grand_billed),
        "grand_paid": str(grand_billed - grand_outstanding),
        "grand_outstanding": str(grand_outstanding),
        "customers": rows,
    }


# ---------------------------------------------------------------------------
# Dispatch (kept for callers that still need a registry)
# ---------------------------------------------------------------------------
TOOL_DISPATCH = {
    "search_customers": search_customers,
    "search_users": search_users,
    "search_suppliers": search_suppliers,
    "search_workers": search_workers,
    "search_projects": search_projects,
    "get_customer_ledgers": get_customer_ledgers,
    "get_supplier_ledgers": get_supplier_ledgers,
    "get_project_workers": get_project_workers,
    "propose_transaction": propose_transaction,
    "propose_supplier_payment": propose_supplier_payment,
    "propose_worker_attendance": propose_worker_attendance,
    "query_customer_balance": query_customer_balance,
    "query_project_expense_summary": query_project_expense_summary,
    "query_supplier_pending": query_supplier_pending,
    "query_project_houses": query_project_houses,
    "query_worker_attendance": query_worker_attendance,
    "query_project_materials": query_project_materials,
    "query_customer_enquiries": query_customer_enquiries,
    "query_property_sell_requests": query_property_sell_requests,
    "query_user_ledger": query_user_ledger,
    "query_project_summary": query_project_summary,
    "query_all_customers_balance": query_all_customers_balance,
}

PROPOSAL_TOOLS = {
    "propose_transaction",
    "propose_supplier_payment",
    "propose_worker_attendance",
}
