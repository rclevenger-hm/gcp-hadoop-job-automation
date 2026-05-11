import functions_framework

from app.handlers import api_handler, reconcile_handler, worker_handler


@functions_framework.http
def api(request):
    return api_handler(request)


@functions_framework.http
def worker(request):
    return worker_handler(request)


@functions_framework.http
def reconcile(request):
    return reconcile_handler(request)
