from django.test import TestCase
from customer.models import PSPUser, Purchase, Deposit, ReceiveableAccount
from localflavor.us.us_states import US_STATES
import random
from datetime import date, timedelta

from faker import Faker
fake = Faker()


"""        user = self.model(
            email=self.normalize_email(email),
            first_name=first,
            last_name=last,
            address1=address1,
            city=city,
            postal_code=postal_code,
            state=state,
            ssn_lastfour=ssn_lastfour,
            date_of_birth=date_of_birth
        )"""


class AnimalTestCase(TestCase):

    email = None

    def setUp(self):

        self.email = fake.email()
        name = fake.name().split()
        city = fake.name().split()[0]
        state = random.choice(US_STATES)[0]
        age = random.randrange(19, 50)
        birthdate = date.today() - timedelta(days=int(age * 365))

        user = PSPUser.objects.create(
            email=self.email,
            first_name=name[0],
            last_name=name[1],
            address1=fake.address()[0:40],
            city=city,
            postal_code='55402',
            state=state,
            ssn_lastfour=random.randrange(1000, 9999),
            date_of_birth=birthdate
        )

    def test_that_user_created_ok(self):

        user = PSPUser.objects.get(email=self.email)
        self.assertEqual(str(user), self.email)

    def test_that_user_has_dwolla_url(self):
        user = PSPUser.objects.get(email=self.email)
        self.assertIsNotNone(user.dwolla_url)
        self.assertIsNotNone(user.dwolla_id)
