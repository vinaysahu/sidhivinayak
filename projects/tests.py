from django.test import TestCase, Client
from django.urls import reverse
from .models.Projects import Projects
from workers.models.Workers import Workers
from workers.models.WorkerTypes import WorkerTypes

class ProjectModelTest(TestCase):
    def setUp(self):
        self.project = Projects.objects.create(
            name='Luxury Apartments',
            area_sqyd=1000,
            project_type=Projects.PROJECT_TYPES_FLOOR
        )

    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Luxury Apartments')
        self.assertEqual(str(self.project), 'Luxury Apartments')

class ProjectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.worker_type = WorkerTypes.objects.create(name='Mason', wages=500)
        self.worker = Workers.objects.create(
            name='Bob',
            worker_type_id=self.worker_type,
            wages=500,
            mobile='9876543210'
        )

    def test_get_worker_wages_ajax(self):
        url = reverse('get-worker-wages')
        response = self.client.get(url, {'worker_id': self.worker.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['wages'], 500)
