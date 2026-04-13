from django.test import TestCase
from .models.Countries import Countries
from .models.States import States
from .models.Cities import Cities
from .models.Suppliers import Suppliers

class GlobalsModelTest(TestCase):
    def setUp(self):
        self.country = Countries.objects.create(name='India')
        self.state = States.objects.create(name='Haryana', country_id=self.country)
        self.city = Cities.objects.create(name='Gurgaon', state_id=self.state)

    def test_location_models(self):
        self.assertEqual(str(self.country), 'India')
        self.assertEqual(str(self.state), 'Haryana')
        self.assertEqual(str(self.city), 'Gurgaon')

    def test_supplier_creation(self):
        supplier = Suppliers.objects.create(
            shop_name='Main Hardware',
            mobile='9876543210'
        )
        self.assertEqual(str(supplier), 'Main Hardware')
