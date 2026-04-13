from django.test import TestCase
from .models.Workers import Workers
from .models.WorkerTypes import WorkerTypes

class WorkerModelTest(TestCase):
    def setUp(self):
        self.worker_type = WorkerTypes.objects.create(name='Electrician', wages=1000)
        self.worker = Workers.objects.create(
            name='Alice',
            worker_type_id=self.worker_type,
            wages=800,
            mobile='9999999999'
        )

    def test_worker_creation(self):
        self.assertEqual(self.worker.name, 'Alice')
        self.assertEqual(str(self.worker), 'Alice')

    def test_worker_type_creation(self):
        self.assertEqual(str(self.worker_type), 'Electrician')
