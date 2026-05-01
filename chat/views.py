"""
Views for the AI Agent chat interface. Superuser-only access.
"""
import json
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Dict, List

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models as db_models
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from customers.models.CustomerLedger import CustomerLedger
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from projects.models.ProjectSupplierLedger import ProjectSupplierLedger
from projects.models.ProjectSupplierPayment import ProjectSupplierPayment
from projects.models.ProjectWorkerAttendances import ProjectWorkerAttendances
from projects.models.ProjectWorkers import ProjectWorkers
from projects.models.Projects import Projects
from workers.models.Workers import Workers
from workers.models.WorkerTypes import WorkerTypes
from globals.models.Suppliers import Suppliers
from globals.models.Brands import Brands
from accounts.models.UserLedger import UserLedger
from accounts.models.UserLedgerTransaction import UserLedgerTransaction
from customers.models.Customers import Customers
from customers.models.CustomerLedger import CustomerLedger
from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
from projects.models.ProjectHouses import ProjectHouses

from .models import ChatSession, ChatMessage, PendingTransaction
from .services.gemini_agent import run_turn
from .services.tools import (
    get_customer_ledgers as _lookup_customer_ledgers_impl,
    search_customers as _search_customers_impl,
    search_users as _search_users_impl,
)
import re as _re


logger = logging.getLogger(__name__)


def _is_superuser(user) -> bool:
    return user.is_authenticated and user.is_superuser


superuser_required = user_passes_test(_is_superuser, login_url="/admin/login/")


def _build_history(session: ChatSession) -> List[Dict]:
    history = []
    for msg in session.messages.all():
        if msg.role not in ("user", "assistant"):
            continue
        content = msg.content if isinstance(msg.content, str) else ""
        if not content:
            continue
        history.append({"role": msg.role, "content": content})
    return history


def _pending_to_dict(p: PendingTransaction) -> dict:
    return {
        "id": p.id,
        "kind": p.kind,
        "status": p.status,
        "payload": p.payload,
        "created_at": p.created_at.isoformat(),
    }


@login_required(login_url="/admin/login/")
@superuser_required
def chat_page(request):
    return render(request, "chat/chat.html")


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def list_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user)
    data = [
        {
            "id": s.id,
            "title": s.title or f"Chat #{s.id}",
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]
    return JsonResponse({"sessions": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def new_session(request):
    session = ChatSession.objects.create(user=request.user, title="")
    return JsonResponse({
        "id": session.id,
        "title": session.title or f"Chat #{session.id}",
        "updated_at": session.updated_at.isoformat(),
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def get_session(request, session_id: int):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = []
    for m in session.messages.all():
        if m.role not in ("user", "assistant"):
            continue
        messages.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        })
    pending = [
        _pending_to_dict(p)
        for p in session.pending_transactions.filter(status=PendingTransaction.STATUS_PENDING)
    ]
    return JsonResponse({
        "id": session.id,
        "title": session.title or f"Chat #{session.id}",
        "messages": messages,
        "pending_transactions": pending,
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def send_message(request, session_id: int):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (body.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "Empty message"}, status=400)

    history = _build_history(session)

    user_msg = ChatMessage.objects.create(
        session=session, role="user", content=text
    )

    if not session.title:
        session.title = text[:60]
        session.save(update_fields=["title", "updated_at"])

    try:
        result = run_turn(history, text)
    except Exception as e:
        logger.exception("AI agent failed")
        return JsonResponse(
            {"error": f"AI agent error: {e}"}, status=500
        )

    assistant_text = result.get("assistant_text") or ""
    if assistant_text:
        ChatMessage.objects.create(
            session=session, role="assistant", content=assistant_text
        )

    pending_dict = None
    proposal = result.get("proposal")
    if proposal:
        kind = proposal.get("kind") or PendingTransaction.KIND_CUSTOMER_TXN
        pending = PendingTransaction.objects.create(
            session=session,
            kind=kind,
            payload=proposal,
        )
        pending_dict = _pending_to_dict(pending)

    session.save(update_fields=["updated_at"])

    return JsonResponse({
        "user_message_id": user_msg.id,
        "assistant_text": assistant_text,
        "pending_transaction": pending_dict,
    })


# ---------------------------------------------------------------------------
# Confirm helpers - one per kind
# ---------------------------------------------------------------------------
def _to_decimal(v, field):
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError):
        raise ValueError(f"{field} '{v}' is not a valid number")


def _confirm_customer_txn(payload: dict) -> dict:
    ledger = CustomerLedger.objects.get(id=payload["customer_ledger_id"])
    paid_to = User.objects.get(id=payload["paid_to_user_id"])
    amount = _to_decimal(payload["amount"], "amount")
    paid_on = date.fromisoformat(payload["paid_on"])
    payment_type = payload["payment_type"]
    if payment_type not in ("credited", "debited"):
        raise ValueError(f"Invalid payment_type: {payment_type}")
    detail = payload.get("detail") or ""

    txn = CustomerLedgerTransaction.objects.create(
        customer_ledger=ledger,
        payment_type=payment_type,
        amount=amount,
        detail=detail,
        paid_on=paid_on,
        paid_to=paid_to,
    )
    customer_name = ledger.customer_id.first_name or ledger.customer_id.username
    paid_to_name = paid_to.first_name or paid_to.username
    return {
        "created_transaction": txn,
        "message": (
            f"Transaction #{txn.id} created for {customer_name}. "
            f"Amount Rs. {amount} ({payment_type}) paid to {paid_to_name}."
        ),
    }


def _confirm_supplier_payment(payload: dict) -> dict:
    sl = ProjectSupplierLedger.objects.get(id=payload["supplier_ledger_id"])
    amount = _to_decimal(payload["payment_amount"], "payment_amount")
    payment_date = date.fromisoformat(payload["payment_date"])
    payment_mode = payload["payment_mode"]
    valid_modes = {"cash", "cheque", "online", "bank_transfer"}
    if payment_mode not in valid_modes:
        raise ValueError(f"Invalid payment_mode: {payment_mode}")
    reference_number = payload.get("reference_number") or None
    notes = payload.get("notes") or None

    sp = ProjectSupplierPayment.objects.create(
        supplier_ledger=sl,
        payment_amount=amount,
        payment_date=payment_date,
        payment_mode=payment_mode,
        reference_number=reference_number,
        notes=notes,
    )
    return {
        "created_supplier_payment": sp,
        "message": (
            f"Supplier payment #{sp.id} of Rs. {amount} to "
            f"{sl.supplier.shop_name} ({sl.project.name}) recorded "
            f"via {payment_mode}."
        ),
    }


def _confirm_worker_attendance(payload: dict) -> dict:
    pw = ProjectWorkers.objects.get(id=payload["project_worker_id"])
    working_date = date.fromisoformat(payload["working_date"])
    total_amount = _to_decimal(payload["total_amount"], "total_amount")
    paid_amount = _to_decimal(payload.get("paid_amount") or 0, "paid_amount")
    remaining_amount = total_amount - paid_amount

    att = ProjectWorkerAttendances.objects.create(
        project_worker_id=pw,
        total_amount=total_amount,
        paid_amount=paid_amount,
        remaining_amount=remaining_amount,
        working_date=working_date,
    )
    return {
        "created_worker_attendance": att,
        "message": (
            f"Attendance #{att.id} recorded for {pw.worker_id.name} on "
            f"{pw.project_id.name} ({working_date.isoformat()}). "
            f"Total Rs. {total_amount}, paid Rs. {paid_amount}, "
            f"remaining Rs. {remaining_amount}."
        ),
    }


CONFIRM_HANDLERS = {
    PendingTransaction.KIND_CUSTOMER_TXN: _confirm_customer_txn,
    PendingTransaction.KIND_SUPPLIER_PAYMENT: _confirm_supplier_payment,
    PendingTransaction.KIND_WORKER_ATTENDANCE: _confirm_worker_attendance,
}


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def confirm_pending(request, pending_id: int):
    pending = get_object_or_404(
        PendingTransaction,
        id=pending_id,
        session__user=request.user,
        status=PendingTransaction.STATUS_PENDING,
    )

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}
    overrides = body.get("overrides") or {}

    payload = dict(pending.payload)
    payload.update({k: v for k, v in overrides.items() if v is not None})

    handler = CONFIRM_HANDLERS.get(pending.kind)
    if handler is None:
        return JsonResponse({"error": f"Unknown pending kind: {pending.kind}"}, status=400)

    try:
        with transaction.atomic():
            result = handler(payload)
            pending.status = PendingTransaction.STATUS_CONFIRMED
            if "created_transaction" in result:
                pending.created_transaction = result["created_transaction"]
            if "created_supplier_payment" in result:
                pending.created_supplier_payment = result["created_supplier_payment"]
            if "created_worker_attendance" in result:
                pending.created_worker_attendance = result["created_worker_attendance"]
            pending.resolved_at = timezone.now()
            pending.payload = payload
            pending.save()
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({"error": f"Invalid payload: {e}"}, status=400)
    except (
        CustomerLedger.DoesNotExist,
        User.DoesNotExist,
        ProjectSupplierLedger.DoesNotExist,
        ProjectWorkers.DoesNotExist,
    ) as e:
        return JsonResponse({"error": f"Referenced record missing: {e}"}, status=400)

    return JsonResponse({
        "ok": True,
        "kind": pending.kind,
        "message": result["message"],
    })


# ---------------------------------------------------------------------------
# Inline-form lookup + quick-create endpoints (no AI agent involved)
# ---------------------------------------------------------------------------
@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def lookup_customers(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    return JsonResponse(_search_customers_impl(q))


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def lookup_users(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    return JsonResponse(_search_users_impl(q))


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def lookup_customer_ledgers(request):
    try:
        customer_id = int(request.GET.get("customer_id") or 0)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid customer_id"}, status=400)
    if not customer_id:
        return JsonResponse({"error": "customer_id required"}, status=400)
    return JsonResponse(_lookup_customer_ledgers_impl(customer_id))


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def quick_create_customer_txn(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["customer_ledger_id", "amount", "payment_type", "paid_on", "paid_to_user_id"]
    missing = [k for k in required if not body.get(k)]
    if missing:
        return JsonResponse({"error": f"Missing fields: {', '.join(missing)}"}, status=400)

    try:
        with transaction.atomic():
            result = _confirm_customer_txn(body)
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({"error": f"Invalid data: {e}"}, status=400)
    except CustomerLedger.DoesNotExist:
        return JsonResponse({"error": "Customer ledger not found"}, status=400)
    except User.DoesNotExist:
        return JsonResponse({"error": "Paid-to user not found"}, status=400)

    return JsonResponse({
        "ok": True,
        "message": result["message"],
        "transaction_id": result["created_transaction"].id,
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def cancel_pending(request, pending_id: int):
    pending = get_object_or_404(
        PendingTransaction,
        id=pending_id,
        session__user=request.user,
        status=PendingTransaction.STATUS_PENDING,
    )
    pending.status = PendingTransaction.STATUS_CANCELLED
    pending.resolved_at = timezone.now()
    pending.save(update_fields=["status", "resolved_at"])
    return JsonResponse({"ok": True})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def translate_text(request):
    try:
        body = json.loads(request.body)
        text = body.get("text", "").strip()
        if not text:
            return JsonResponse({"translated_text": ""})

        from .services.gemini_agent import _build_llm
        from langchain_core.messages import HumanMessage
        
        llm = _build_llm()
        prompt = f"Translate the following Hindi text to English. Return ONLY the translated English text and nothing else:\n\n{text}"
        response = llm.invoke([HumanMessage(content=prompt)])
        translated = response.content.strip() if hasattr(response, 'content') else str(response)

        return JsonResponse({"translated_text": translated})
    except Exception as e:
        logger.exception("Translation failed")
        return JsonResponse({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# Project Workers chatbot API endpoints
# ---------------------------------------------------------------------------

@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def get_worker_types(request):
    types = list(WorkerTypes.objects.all().values("id", "name", "wages"))
    return JsonResponse({"types": types})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def create_global_worker(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["name", "worker_type_id", "wages", "wages_type", "mobile"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required fields: {', '.join(missing)}"}, status=400)

    try:
        worker_type = WorkerTypes.objects.get(id=int(body["worker_type_id"]))
    except (WorkerTypes.DoesNotExist, ValueError):
        return JsonResponse({"error": "Worker type not found"}, status=400)

    try:
        worker = Workers(
            name=body["name"].strip(),
            worker_type_id=worker_type,
            wages=int(body["wages"]),
            wages_type=int(body["wages_type"]),
            mobile=body["mobile"].strip(),
            ratting=int(body["ratting"]) if body.get("ratting") else None,
            status=int(body.get("status") or Workers.STATUS_ACTIVE),
        )
        worker.full_clean()
        worker.save()
    except ValidationError as e:
        errors = {}
        if hasattr(e, "message_dict"):
            errors = {k: ", ".join(v) for k, v in e.message_dict.items()}
        else:
            errors = {"__all__": str(e)}
        return JsonResponse({"error": errors}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "worker": {"id": worker.id, "name": worker.name}})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def project_search(request):
    q = (request.GET.get("q") or "").strip()
    qs = Projects.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    data = [{"id": p.id, "name": p.name} for p in qs[:20]]
    return JsonResponse({"projects": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def project_unassigned_workers(request, project_id):
    project = get_object_or_404(Projects, id=project_id)
    assigned_ids = ProjectWorkers.objects.filter(
        project_id=project, status=ProjectWorkers.STATUS_ACTIVE
    ).values_list("worker_id_id", flat=True)
    workers = Workers.objects.filter(status=Workers.STATUS_ACTIVE).exclude(id__in=assigned_ids)
    data = [
        {
            "id": w.id,
            "name": w.name,
            "wages_type": w.wages_type,
            "wages_type_display": w.get_wages_type_display(),
            "wages": w.wages,
            "mobile": w.mobile,
        }
        for w in workers
    ]
    return JsonResponse({"workers": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def project_assign_workers(request, project_id):
    project = get_object_or_404(Projects, id=project_id)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    assigned = skipped = 0
    for wd in body.get("workers", []):
        try:
            worker = Workers.objects.get(id=int(wd["worker_id"]))
        except (Workers.DoesNotExist, KeyError, ValueError):
            skipped += 1
            continue
        if ProjectWorkers.objects.filter(
            project_id=project, worker_id=worker, status=ProjectWorkers.STATUS_ACTIVE
        ).exists():
            skipped += 1
            continue
        ProjectWorkers.objects.create(
            project_id=project,
            worker_id=worker,
            wages=int(wd.get("wages") or worker.wages),
            wages_type=int(wd.get("wages_type") or worker.wages_type),
        )
        assigned += 1

    return JsonResponse({"ok": True, "assigned": assigned, "skipped": skipped})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def project_workers_by_wages_type(request, project_id, wages_type):
    project = get_object_or_404(Projects, id=project_id)
    pws = ProjectWorkers.objects.filter(
        project_id=project, wages_type=wages_type, status=ProjectWorkers.STATUS_ACTIVE
    ).select_related("worker_id")
    data = []
    for pw in pws:
        total_paid = (
            ProjectWorkerAttendances.objects.filter(project_worker_id=pw)
            .aggregate(t=Sum("paid_amount"))["t"] or Decimal("0")
        )
        data.append({
            "pw_id": pw.id,
            "worker_id": pw.worker_id.id,
            "worker_name": pw.worker_id.name,
            "wages": float(pw.wages),
            "total_paid": float(total_paid),
        })
    return JsonResponse({"workers": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def mark_per_day_attendance(request, project_id):
    project = get_object_or_404(Projects, id=project_id)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    today = timezone.now().date()
    marked = skipped = 0
    for pw_id in body.get("project_worker_ids", []):
        try:
            pw = ProjectWorkers.objects.get(id=int(pw_id), project_id=project)
        except (ProjectWorkers.DoesNotExist, ValueError):
            skipped += 1
            continue
        if ProjectWorkerAttendances.objects.filter(project_worker_id=pw, working_date=today).exists():
            skipped += 1
            continue
        ProjectWorkerAttendances.objects.create(
            project_worker_id=pw,
            total_amount=pw.wages,
            paid_amount=Decimal("0"),
            remaining_amount=pw.wages,
            working_date=today,
        )
        marked += 1

    return JsonResponse({"ok": True, "marked": marked, "skipped": skipped})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def pay_per_day_workers(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    today = timezone.now().date()
    updated = 0
    for p in body.get("payments", []):
        try:
            pw = ProjectWorkers.objects.get(id=int(p["project_worker_id"]))
            amount = Decimal(str(p["amount"]))
        except (ProjectWorkers.DoesNotExist, KeyError, ValueError, InvalidOperation):
            continue
        last_att = (
            ProjectWorkerAttendances.objects.filter(project_worker_id=pw)
            .order_by("-working_date", "-id")
            .first()
        )
        if not last_att:
            continue
        old_paid = last_att.paid_amount or Decimal("0")
        new_paid = old_paid + amount
        new_remaining = (last_att.total_amount or Decimal("0")) - new_paid
        last_att.paid_amount = new_paid
        last_att.remaining_amount = new_remaining
        last_att.payment_date = today
        last_att.save(update_fields=["paid_amount", "remaining_amount", "payment_date", "updated_at"])
        updated += 1

    return JsonResponse({"ok": True, "updated": updated})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def project_worker_detail(request, pw_id):
    pw = get_object_or_404(ProjectWorkers, id=pw_id)
    total_paid = (
        ProjectWorkerAttendances.objects.filter(project_worker_id=pw)
        .aggregate(t=Sum("paid_amount"))["t"] or Decimal("0")
    )
    return JsonResponse({
        "pw_id": pw.id,
        "worker_name": pw.worker_id.name,
        "wages": float(pw.wages),
        "wages_type": pw.wages_type,
        "total_paid": float(total_paid),
        "balance": float(Decimal(str(pw.wages)) - total_paid),
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def lum_sum_pay(request, pw_id):
    pw = get_object_or_404(ProjectWorkers, id=pw_id)
    try:
        body = json.loads(request.body)
        amount = Decimal(str(body.get("amount", 0)))
    except (json.JSONDecodeError, InvalidOperation):
        return JsonResponse({"error": "Invalid amount"}, status=400)
    if amount <= 0:
        return JsonResponse({"error": "Amount must be > 0"}, status=400)

    total_paid_before = (
        ProjectWorkerAttendances.objects.filter(project_worker_id=pw)
        .aggregate(t=Sum("paid_amount"))["t"] or Decimal("0")
    )
    remaining = Decimal(str(pw.wages)) - total_paid_before - amount
    today = timezone.now().date()
    ProjectWorkerAttendances.objects.create(
        project_worker_id=pw,
        total_amount=pw.wages,
        paid_amount=amount,
        remaining_amount=remaining,
        working_date=today,
        payment_date=today,
    )
    return JsonResponse({"ok": True})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def per_hour_pay(request, pw_id):
    pw = get_object_or_404(ProjectWorkers, id=pw_id)
    try:
        body = json.loads(request.body)
        hours = Decimal(str(body.get("hours", 0)))
        amount = Decimal(str(body.get("amount", 0)))
    except (json.JSONDecodeError, InvalidOperation):
        return JsonResponse({"error": "Invalid data"}, status=400)
    if not hours or hours <= 0:
        return JsonResponse({"error": "Hours required and must be > 0"}, status=400)

    total_amount = hours * Decimal(str(pw.wages))
    remaining = total_amount - amount
    today = timezone.now().date()
    ProjectWorkerAttendances.objects.create(
        project_worker_id=pw,
        total_amount=total_amount,
        paid_amount=amount,
        remaining_amount=remaining,
        hours=hours,
        working_date=today,
        payment_date=today if amount > 0 else None,
    )
    return JsonResponse({"ok": True})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def per_sqft_pay(request, pw_id):
    pw = get_object_or_404(ProjectWorkers, id=pw_id)
    try:
        body = json.loads(request.body)
        amount = Decimal(str(body.get("amount", 0)))
    except (json.JSONDecodeError, InvalidOperation):
        return JsonResponse({"error": "Invalid amount"}, status=400)
    if amount <= 0:
        return JsonResponse({"error": "Amount must be > 0"}, status=400)

    total_paid_before = (
        ProjectWorkerAttendances.objects.filter(project_worker_id=pw)
        .aggregate(t=Sum("paid_amount"))["t"] or Decimal("0")
    )
    today = timezone.now().date()
    ProjectWorkerAttendances.objects.create(
        project_worker_id=pw,
        total_amount=None,
        paid_amount=amount,
        remaining_amount=None,
        working_date=today,
        payment_date=today,
    )
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# Project Suppliers chatbot API endpoints
# ---------------------------------------------------------------------------

@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def get_brands(request):
    brands = list(Brands.objects.filter(status=10).values("id", "name"))
    return JsonResponse({"brands": brands})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def create_global_supplier(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["shop_name", "mobile"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required fields: {', '.join(missing)}"}, status=400)

    brand = None
    if body.get("brand_id"):
        try:
            brand = Brands.objects.get(id=int(body["brand_id"]))
        except (Brands.DoesNotExist, ValueError):
            return JsonResponse({"error": "Brand not found"}, status=400)

    try:
        supplier = Suppliers(
            shop_name=body["shop_name"].strip(),
            mobile=body["mobile"].strip(),
            first_name=(body.get("first_name") or "").strip() or None,
            last_name=(body.get("last_name") or "").strip() or None,
            address=(body.get("address") or "").strip() or None,
            brand_id=brand,
            status=int(body.get("status") or 10),
        )
        supplier.full_clean()
        supplier.save()
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            msg = {k: ", ".join(v) for k, v in e.message_dict.items()}
        else:
            msg = str(e)
        return JsonResponse({"error": msg}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "supplier": {"id": supplier.id, "name": supplier.shop_name}})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def supplier_search(request):
    q = (request.GET.get("q") or "").strip()
    qs = Suppliers.objects.filter(status=10)
    if q:
        qs = qs.filter(shop_name__icontains=q)
    data = [{"id": s.id, "name": s.shop_name, "mobile": s.mobile} for s in qs[:20]]
    return JsonResponse({"suppliers": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def project_supplier_ledgers(request, project_id):
    project = get_object_or_404(Projects, id=project_id)
    q = (request.GET.get("q") or "").strip()
    qs = ProjectSupplierLedger.objects.filter(project=project).select_related("supplier")
    if q:
        qs = qs.filter(supplier__shop_name__icontains=q)
    data = [
        {
            "id": sl.id,
            "supplier_name": sl.supplier.shop_name,
            "item_description": sl.item_description,
            "item_date": sl.item_date.isoformat(),
            "total_amount": float(sl.total_amount),
            "paid_amount": float(sl.paid_amount),
            "balance": float(sl.balance),
        }
        for sl in qs[:30]
    ]
    return JsonResponse({"ledgers": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def create_project_supplier_ledger(request, project_id):
    project = get_object_or_404(Projects, id=project_id)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["supplier_id", "item_description", "item_date", "total_amount"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required fields: {', '.join(missing)}"}, status=400)

    try:
        supplier = Suppliers.objects.get(id=int(body["supplier_id"]))
    except (Suppliers.DoesNotExist, ValueError):
        return JsonResponse({"error": "Supplier not found"}, status=400)

    try:
        paid = Decimal(str(body.get("paid_amount") or "0"))
        total = Decimal(str(body["total_amount"]))
        item_date = date.fromisoformat(body["item_date"])
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    try:
        ledger = ProjectSupplierLedger(
            project=project,
            supplier=supplier,
            item_description=body["item_description"].strip(),
            item_date=item_date,
            total_amount=total,
            paid_amount=paid,
            notes=(body.get("notes") or "").strip() or None,
        )
        ledger.full_clean()
        ledger.save()
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            msg = {k: ", ".join(v) for k, v in e.message_dict.items()}
        else:
            msg = str(e)
        return JsonResponse({"error": msg}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "ledger": {"id": ledger.id}})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def supplier_ledger_detail(request, ledger_id):
    sl = get_object_or_404(ProjectSupplierLedger, id=ledger_id)
    payments = [
        {
            "id": p.id,
            "payment_amount": float(p.payment_amount),
            "payment_date": p.payment_date.isoformat(),
            "payment_mode": p.payment_mode,
            "reference_number": p.reference_number or "",
            "notes": p.notes or "",
        }
        for p in sl.payments.all()
    ]
    return JsonResponse({
        "id": sl.id,
        "supplier_name": sl.supplier.shop_name,
        "project_name": sl.project.name,
        "item_description": sl.item_description,
        "item_date": sl.item_date.isoformat(),
        "total_amount": float(sl.total_amount),
        "paid_amount": float(sl.paid_amount),
        "balance": float(sl.balance),
        "notes": sl.notes or "",
        "payments": payments,
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def add_supplier_payment(request, ledger_id):
    sl = get_object_or_404(ProjectSupplierLedger, id=ledger_id)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["payment_amount", "payment_date", "payment_mode"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required fields: {', '.join(missing)}"}, status=400)

    valid_modes = {"cash", "cheque", "online", "bank_transfer"}
    if body["payment_mode"] not in valid_modes:
        return JsonResponse({"error": "Invalid payment mode"}, status=400)

    try:
        amount = Decimal(str(body["payment_amount"]))
        pay_date = date.fromisoformat(body["payment_date"])
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    if amount <= 0:
        return JsonResponse({"error": "Payment amount must be > 0"}, status=400)

    try:
        payment = ProjectSupplierPayment(
            supplier_ledger=sl,
            payment_amount=amount,
            payment_date=pay_date,
            payment_mode=body["payment_mode"],
            reference_number=(body.get("reference_number") or "").strip() or None,
            notes=(body.get("notes") or "").strip() or None,
        )
        payment.full_clean()
        payment.save()
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            msg = {k: ", ".join(v) for k, v in e.message_dict.items()}
        else:
            msg = str(e)
        return JsonResponse({"error": msg}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "payment_id": payment.id})


# ---------------------------------------------------------------------------
# User Ledger chatbot API endpoints
# ---------------------------------------------------------------------------

@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def all_users_list(request):
    users = User.objects.filter(is_active=True).order_by("first_name", "username")
    data = [
        {"id": u.id, "name": (u.get_full_name() or u.username).strip()}
        for u in users
    ]
    return JsonResponse({"users": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def user_ledger_list(request):
    q = (request.GET.get("q") or "").strip()
    project_id = request.GET.get("project_id")
    debtor_id = request.GET.get("debtor_id")

    qs = UserLedger.objects.select_related("creditor", "debtor", "project_id").order_by("-updated_at")

    if q:
        qs = qs.filter(
            Q(creditor__first_name__icontains=q)
            | Q(creditor__last_name__icontains=q)
            | Q(creditor__username__icontains=q)
            | Q(debtor__first_name__icontains=q)
            | Q(debtor__last_name__icontains=q)
            | Q(debtor__username__icontains=q)
        )
    if project_id:
        try:
            qs = qs.filter(project_id_id=int(project_id))
        except ValueError:
            pass
    if debtor_id:
        try:
            qs = qs.filter(debtor_id=int(debtor_id))
        except ValueError:
            pass

    data = [
        {
            "id": ul.id,
            "creditor_name": (ul.creditor.get_full_name() or ul.creditor.username).strip(),
            "debtor_name": (ul.debtor.get_full_name() or ul.debtor.username).strip(),
            "project_name": ul.project_id.name,
            "amount": float(ul.amount),
            "balance": float(ul.balance),
        }
        for ul in qs[:40]
    ]
    return JsonResponse({"ledgers": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def create_user_ledger(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["creditor_id", "debtor_id", "project_id", "amount"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required fields: {', '.join(missing)}"}, status=400)

    try:
        creditor = User.objects.get(id=int(body["creditor_id"]))
        debtor = User.objects.get(id=int(body["debtor_id"]))
        project = Projects.objects.get(id=int(body["project_id"]))
        amount = Decimal(str(body["amount"]))
        balance = Decimal(str(body.get("balance") or body["amount"]))
    except User.DoesNotExist as e:
        return JsonResponse({"error": f"User not found: {e}"}, status=400)
    except Projects.DoesNotExist:
        return JsonResponse({"error": "Project not found"}, status=400)
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    if amount <= 0:
        return JsonResponse({"error": "Amount must be > 0"}, status=400)

    try:
        ledger = UserLedger(
            creditor=creditor,
            debtor=debtor,
            project_id=project,
            amount=amount,
            balance=balance,
        )
        ledger.full_clean()
        ledger.save()
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            msg = {k: ", ".join(v) for k, v in e.message_dict.items()}
        else:
            msg = str(e)
        return JsonResponse({"error": msg}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "ledger_id": ledger.id})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def user_ledger_detail(request, ledger_id):
    ul = get_object_or_404(UserLedger, id=ledger_id)
    transactions = [
        {
            "id": t.id,
            "payment_type": t.payment_type,
            "amount": float(t.amount),
            "paid_on": t.paid_on.isoformat() if t.paid_on else "",
            "detail": t.detail or "",
        }
        for t in ul.transactions.order_by("-paid_on", "-id")[:6]
    ]
    return JsonResponse({
        "id": ul.id,
        "creditor_name": (ul.creditor.get_full_name() or ul.creditor.username).strip(),
        "debtor_name": (ul.debtor.get_full_name() or ul.debtor.username).strip(),
        "project_name": ul.project_id.name,
        "amount": float(ul.amount),
        "balance": float(ul.balance),
        "transactions": transactions,
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def add_user_ledger_transaction(request, ledger_id):
    ul = get_object_or_404(UserLedger, id=ledger_id)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["payment_type", "amount", "paid_on"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required fields: {', '.join(missing)}"}, status=400)

    if body["payment_type"] not in ("credited", "debited"):
        return JsonResponse({"error": "payment_type must be 'credited' or 'debited'"}, status=400)

    try:
        amount = Decimal(str(body["amount"]))
        paid_on = date.fromisoformat(body["paid_on"])
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    if amount <= 0:
        return JsonResponse({"error": "Amount must be > 0"}, status=400)

    try:
        txn = UserLedgerTransaction(
            user_ledger=ul,
            payment_type=body["payment_type"],
            amount=amount,
            paid_on=paid_on,
            detail=(body.get("detail") or "").strip() or None,
        )
        txn.full_clean()
        txn.save()
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            msg = {k: ", ".join(v) for k, v in e.message_dict.items()}
        else:
            msg = str(e)
        return JsonResponse({"error": msg}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "transaction_id": txn.id})


# ---------------------------------------------------------------------------
# Context-aware message parsing + smart form flow
# ---------------------------------------------------------------------------

_SKIP_WORDS = {
    'aaj', 'kal', 'please', 'karo', 'kare', 'karein', 'mai', 'mae', 'mein',
    'me', 'add', 'kro', 'paid', 'ledger', 'description', 'desc', 'detail',
    'amount', 'credit', 'debit', 'date', 'project', 'sorry', 'main', 'and',
    'or', 'super', 'admin', 'superadmin', 'today', 'yesterday', 'transaction',
    'payment', 'user', 'customer', 'worker', 'supplier', 'credited', 'debited',
    'select', 'create', 'show', 'list', 'search', 'karna', 'dena', 'milega',
    'rupee', 'rupees', 'rs', 'inr', 'the', 'and', 'for', 'with', 'from',
    'this', 'that', 'aur', 'toh', 'yeh', 'woh', 'iska', 'uska', 'unka',
    'mere', 'mera', 'tera', 'apna', 'agar', 'phir', 'baad', 'pehle',
    'dikhe', 'dikhao', 'batao', 'kho', 'dalo',
    # common nouns / verbs often found near names — must not be extracted as names
    'carpenter', 'saman', 'material', 'labour', 'labor', 'work', 'kam',
    'diye', 'diya', 'dena', 'liya', 'liye', 'karwayi', 'karwai', 'karaya',
    'nae', 'wale', 'wali', 'wala', 'ko', 'ka', 'ki', 'ke',
}


def _parse_message_entities(text: str) -> dict:
    """Extract name, amount, payment_type, paid_to, detail, date from message."""
    result = {
        "name": None, "amount": None, "payment_type": None,
        "paid_to_name": None, "detail": None, "date": None,
        "project_hint": None,
    }
    t = text.strip()

    # Amount: match number before optional k/thousand/hajar
    amt_m = _re.search(
        r'\b(\d[\d,]*(?:\.\d+)?)\s*(k|K|thousand|hajar)?\b', t
    )
    if amt_m:
        try:
            num = float(amt_m.group(1).replace(',', ''))
            result["amount"] = num * (1000 if amt_m.group(2) else 1)
        except ValueError:
            pass

    # Payment type
    if _re.search(r'\b(credit(?:ed)?|jama)\b', t, _re.IGNORECASE):
        result["payment_type"] = "credited"
    if _re.search(r'\b(debit(?:ed)?|kata|minus|cut)\b', t, _re.IGNORECASE):
        result["payment_type"] = "debited"

    # Paid to: "paid_to mae superadmin" / "paid to superadmin"
    paid_m = _re.search(
        r'paid[_ ]to\s+(?:mae\s+|mein\s+|me\s+|ko\s+)?(\w+)',
        t, _re.IGNORECASE
    )
    if paid_m:
        result["paid_to_name"] = paid_m.group(1).strip()

    # Detail: "description mae add kro carpenter..." / "detail mae ..."
    detail_m = _re.search(
        r'(?:description|detail|desc)\s+(?:mae\s+|mein\s+|me\s+)?'
        r'(?:add\s+kro\s+|likhna\s+|add\s+karna\s+)?(.+?)(?:\s*paid[_ ]to|\s*$)',
        t, _re.IGNORECASE | _re.DOTALL
    )
    if detail_m:
        result["detail"] = detail_m.group(1).strip().rstrip(' or').strip()

    # Date
    if _re.search(r'\baaj\b|\btoday\b', t, _re.IGNORECASE):
        result["date"] = date.today().isoformat()
    elif _re.search(r'\bkal\b|\byesterday\b', t, _re.IGNORECASE):
        from datetime import timedelta
        result["date"] = (date.today() - timedelta(days=1)).isoformat()
    else:
        dm = _re.search(r'\b(\d{4}-\d{2}-\d{2})\b', t)
        if dm:
            result["date"] = dm.group(1)
        else:
            dm2 = _re.search(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b', t)
            if dm2:
                try:
                    dd, mm, yy = int(dm2.group(1)), int(dm2.group(2)), int(dm2.group(3))
                    if yy < 100:
                        yy += 2000
                    result["date"] = f"{yy}-{mm:02d}-{dd:02d}"
                except Exception:
                    pass
    if not result["date"]:
        result["date"] = date.today().isoformat()

    # Project hint: "project Sunshine" / "Sunshine project"
    ph = _re.search(
        r'\bproject\s+([A-Za-z][A-Za-z0-9 ]{1,30}?)(?:\s+(?:mae|mein|se|ka|ki|ke|par|sae)|$)',
        t, _re.IGNORECASE
    )
    if ph:
        result["project_hint"] = ph.group(1).strip()

    # Name extraction
    # Strategy 0: word before "nae"/"ne" — Hindi subject postposition (most reliable)
    ne_m = _re.search(r'\b([A-Za-z]{3,})\s+(?:nae|ne)\b', t, _re.IGNORECASE)
    if ne_m:
        candidate = ne_m.group(1)
        if candidate.lower() not in _SKIP_WORDS:
            result["name"] = candidate
    # Strategy 1: word before ke/ka/ki (Hindi possessive)
    if not result["name"]:
        ke_m = _re.search(r'\b([A-Za-z]{3,})\s+k[aei]\b', t, _re.IGNORECASE)
        if ke_m:
            candidate = ke_m.group(1)
            if candidate.lower() not in _SKIP_WORDS:
                result["name"] = candidate
    # Strategy 2: word before "ledger"
    if not result["name"]:
        led_m = _re.search(
            r'\b([A-Za-z]{3,})\s+(?:ka\s+|ki\s+|ke\s+)?ledger\b',
            t, _re.IGNORECASE
        )
        if led_m:
            c = led_m.group(1)
            if c.lower() not in _SKIP_WORDS:
                result["name"] = c
    # Strategy 3: first non-common word of length >= 3
    if not result["name"]:
        for word in t.split():
            clean = _re.sub(r'[^a-zA-Z]', '', word)
            if len(clean) >= 3 and clean.lower() not in _SKIP_WORDS:
                result["name"] = clean
                break

    return result


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def parse_context(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (body.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "Empty text"}, status=400)

    parsed = _parse_message_entities(text)

    customer_matches, user_matches, paid_to_matches, project_matches = [], [], [], []

    if parsed.get("name"):
        c = _search_customers_impl(parsed["name"])
        customer_matches = c.get("results", [])
        u = _search_users_impl(parsed["name"])
        user_matches = u.get("results", [])

    if parsed.get("paid_to_name"):
        pt = _search_users_impl(parsed["paid_to_name"])
        paid_to_matches = pt.get("results", [])

    if parsed.get("project_hint"):
        from .services.tools import search_projects as _sp
        pr = _sp(parsed["project_hint"])
        project_matches = pr.get("results", [])

    return JsonResponse({
        "parsed": parsed,
        "customer_matches": customer_matches,
        "user_matches": user_matches,
        "paid_to_matches": paid_to_matches,
        "project_matches": project_matches,
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def customer_ledger_for_project(request):
    customer_id = request.GET.get("customer_id")
    project_id = request.GET.get("project_id")
    if not customer_id or not project_id:
        return JsonResponse({"error": "customer_id and project_id required"}, status=400)
    try:
        ledgers = CustomerLedger.objects.filter(
            customer_id_id=int(customer_id),
            project_id_id=int(project_id),
        ).select_related("project_house_id")
        data = [
            {
                "id": l.id,
                "house_label": f"Plot {l.project_house_id.plot_no}" if l.project_house_id else str(l.id),
                "amount": float(l.amount),
                "balance": float(l.balance),
            }
            for l in ledgers
        ]
    except ValueError:
        return JsonResponse({"error": "Invalid IDs"}, status=400)
    return JsonResponse({"ledgers": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def project_houses_list(request):
    project_id = request.GET.get("project_id")
    if not project_id:
        return JsonResponse({"error": "project_id required"}, status=400)
    houses = ProjectHouses.objects.filter(project_id_id=int(project_id)).order_by("plot_no")
    data = [{"id": h.id, "label": f"Plot {h.plot_no} ({h.area_sqyd} sqyd)"} for h in houses]
    return JsonResponse({"houses": data})


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def create_customer_ledger_chatbot(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["customer_id", "project_id", "project_house_id", "amount"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required: {', '.join(missing)}"}, status=400)

    try:
        customer = Customers.objects.get(id=int(body["customer_id"]))
        project = Projects.objects.get(id=int(body["project_id"]))
        house = ProjectHouses.objects.get(id=int(body["project_house_id"]))
        amount = Decimal(str(body["amount"]))
        balance = Decimal(str(body.get("balance") or body["amount"]))
    except (Customers.DoesNotExist, Projects.DoesNotExist, ProjectHouses.DoesNotExist) as e:
        return JsonResponse({"error": str(e)}, status=400)
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    ledger = CustomerLedger.objects.create(
        customer_id=customer,
        project_id=project,
        project_house_id=house,
        amount=amount,
        balance=balance,
    )
    return JsonResponse({"ok": True, "ledger_id": ledger.id})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def customer_ledger_chatbot_detail(request, ledger_id):
    cl = get_object_or_404(CustomerLedger, id=ledger_id)
    txns = [
        {
            "id": t.id,
            "payment_type": t.payment_type,
            "amount": float(t.amount),
            "paid_on": t.paid_on.isoformat() if t.paid_on else "",
            "paid_to": (t.paid_to.get_full_name() or t.paid_to.username).strip(),
            "detail": t.detail or "",
        }
        for t in cl.customer_ledger_transactions.order_by("-paid_on", "-id")[:6]
    ]
    customer_name = " ".join(filter(None, [cl.customer_id.first_name, cl.customer_id.last_name])).strip() \
                    or cl.customer_id.username
    house_label = f"Plot {cl.project_house_id.plot_no}" if cl.project_house_id else str(cl.id)
    return JsonResponse({
        "id": cl.id,
        "customer_name": customer_name,
        "project_name": cl.project_id.name,
        "house_label": house_label,
        "amount": float(cl.amount),
        "balance": float(cl.balance),
        "transactions": txns,
    })


@login_required(login_url="/admin/login/")
@superuser_required
@require_POST
def add_customer_ledger_transaction(request, ledger_id):
    cl = get_object_or_404(CustomerLedger, id=ledger_id)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["payment_type", "amount", "paid_on", "paid_to_user_id"]
    missing = [k for k in required if not str(body.get(k, "")).strip()]
    if missing:
        return JsonResponse({"error": f"Required: {', '.join(missing)}"}, status=400)

    if body["payment_type"] not in ("credited", "debited"):
        return JsonResponse({"error": "payment_type must be credited or debited"}, status=400)

    try:
        amount = Decimal(str(body["amount"]))
        paid_on = date.fromisoformat(body["paid_on"])
        paid_to = User.objects.get(id=int(body["paid_to_user_id"]))
    except (User.DoesNotExist,):
        return JsonResponse({"error": "paid_to user not found"}, status=400)
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    if amount <= 0:
        return JsonResponse({"error": "Amount must be > 0"}, status=400)

    try:
        txn = CustomerLedgerTransaction(
            customer_ledger=cl,
            payment_type=body["payment_type"],
            amount=amount,
            paid_on=paid_on,
            paid_to=paid_to,
            detail=(body.get("detail") or "").strip() or None,
        )
        txn.full_clean()
        txn.save()
    except ValidationError as e:
        msg = {k: ", ".join(v) for k, v in e.message_dict.items()} if hasattr(e, "message_dict") else str(e)
        return JsonResponse({"error": msg}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"ok": True, "transaction_id": txn.id})


@login_required(login_url="/admin/login/")
@superuser_required
@require_GET
def user_ledgers_for_creditor(request):
    user_id = request.GET.get("user_id")
    project_id = request.GET.get("project_id")
    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)
    qs = UserLedger.objects.filter(creditor_id=int(user_id)).select_related("debtor", "project_id")
    if project_id:
        qs = qs.filter(project_id_id=int(project_id))
    data = [
        {
            "id": ul.id,
            "debtor_name": (ul.debtor.get_full_name() or ul.debtor.username).strip(),
            "project_name": ul.project_id.name,
            "amount": float(ul.amount),
            "balance": float(ul.balance),
        }
        for ul in qs
    ]
    return JsonResponse({"ledgers": data})
