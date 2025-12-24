from django.http import JsonResponse
from workers.models.Workers import Workers

def get_worker_wages(request):
    worker_id = request.GET.get("worker_id")

    try:
        worker = Workers.objects.get(id=worker_id)
        return JsonResponse({"wages": worker.wages, "type": worker.wages_type})
    except Workers.DoesNotExist:
        return JsonResponse({"wages": 0, 'type':10})
