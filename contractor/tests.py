from django.test import TestCase
from .models.Projects import Projects
from workers.models.Workers import Workers
from workers.models.WorkerTypes import WorkerTypes
from .models.ProjectWorkers import ProjectWorkers

class ContractorModelTest(TestCase):
    def setUp(self):
        self.project = Projects.objects.create(name='Contractor Proj', area_sqyd=500)
        self.worker_type = WorkerTypes.objects.create(name='Plumber', wages=600)
        self.worker = Workers.objects.create(name='Charlie', worker_type_id=self.worker_type, wages=600, mobile='8888888888')

    def test_contractor_project_creation(self):
        self.assertEqual(str(self.project), 'Contractor Proj')

    def test_project_worker_creation(self):
        pw = ProjectWorkers.objects.create(
            project_id=self.project,
            worker_id=self.worker,
            wages=600
        )
        self.assertEqual(str(pw), 'Contractor Proj')
