from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from user_auth.models import Company, Role, User
from accounting.models import Expense
from core.models import RecordDeletionLog


class RecycleBinTests(TestCase):
    """End-to-end coverage for Phase 1: soft-delete, recycle bin list/restore/purge/
    empty, Owner/Manager-only gating, and the deletion audit log. Runs against Django's
    isolated per-run test database, not production data."""

    def setUp(self):
        self.company = Company.objects.create(name='Test Shop')
        self.owner_role = Role.objects.create(name='Owner', level=1)
        self.cashier_role = Role.objects.create(name='Cashier', level=3)
        self.owner = User.objects.create_user(
            email='owner@test.local', password='x', company=self.company, role=self.owner_role,
        )
        self.cashier = User.objects.create_user(
            email='cashier@test.local', password='x', company=self.company, role=self.cashier_role,
        )
        self.client = APIClient()

    def _make_expense(self):
        return Expense.objects.create(
            company=self.company, category='other', amount=1.23,
            expense_date=date.today(), description='disposable', recorded_by=self.owner,
        )

    def test_non_admin_cannot_delete(self):
        exp = self._make_expense()
        self.client.force_authenticate(user=self.cashier)
        r = self.client.delete(f'/api/accounting/expenses/{exp.id}/')
        self.assertEqual(r.status_code, 403)

    def test_owner_soft_delete_hides_from_list_and_appears_in_bin(self):
        exp = self._make_expense()
        self.client.force_authenticate(user=self.owner)

        r = self.client.delete(f'/api/accounting/expenses/{exp.id}/')
        self.assertEqual(r.status_code, 204)

        exp.refresh_from_db()
        self.assertTrue(exp.is_deleted)
        self.assertIsNotNone(exp.deleted_at)
        self.assertEqual(exp.deleted_by_id, self.owner.id)

        r = self.client.get('/api/accounting/expenses/')
        self.assertNotIn(exp.id, [e['id'] for e in r.json()['results']])

        r = self.client.get('/api/core/recycle-bin/')
        items = r.json()['results']
        match = next((i for i in items if i['model'] == 'accounting.expense' and i['id'] == exp.id), None)
        self.assertIsNotNone(match)
        self.assertEqual(match['deleted_by'], self.owner.email)

        log = RecordDeletionLog.objects.get(object_id=exp.id, action='deleted')
        self.assertEqual(log.performed_by_id, self.owner.id)

    def test_restore_brings_it_back(self):
        exp = self._make_expense()
        self.client.force_authenticate(user=self.owner)
        self.client.delete(f'/api/accounting/expenses/{exp.id}/')

        r = self.client.post('/api/core/recycle-bin/restore/', {'model': 'accounting.expense', 'id': exp.id}, format='json')
        self.assertEqual(r.status_code, 200)

        exp.refresh_from_db()
        self.assertFalse(exp.is_deleted)
        self.assertIsNone(exp.deleted_at)

        r = self.client.get('/api/accounting/expenses/')
        self.assertIn(exp.id, [e['id'] for e in r.json()['results']])
        self.assertTrue(RecordDeletionLog.objects.filter(object_id=exp.id, action='restored').exists())

    def test_purge_actually_removes_the_row(self):
        exp = self._make_expense()
        self.client.force_authenticate(user=self.owner)
        self.client.delete(f'/api/accounting/expenses/{exp.id}/')

        r = self.client.post('/api/core/recycle-bin/purge/', {'model': 'accounting.expense', 'id': exp.id}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Expense.all_objects.filter(pk=exp.id).exists())
        self.assertTrue(RecordDeletionLog.objects.filter(object_id=exp.id, action='purged').exists())

    def test_empty_bin_purges_everything_deleted(self):
        exp1, exp2 = self._make_expense(), self._make_expense()
        self.client.force_authenticate(user=self.owner)
        self.client.delete(f'/api/accounting/expenses/{exp1.id}/')
        self.client.delete(f'/api/accounting/expenses/{exp2.id}/')

        r = self.client.post('/api/core/recycle-bin/empty/', {}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.json()['purged_count'], 2)
        self.assertFalse(Expense.all_objects.filter(pk__in=[exp1.id, exp2.id]).exists())

    def test_non_admin_cannot_hit_recycle_bin(self):
        self.client.force_authenticate(user=self.cashier)
        r = self.client.get('/api/core/recycle-bin/')
        self.assertEqual(r.status_code, 403)


class PaginationFilterSortTests(TestCase):
    """Phase 2: every list endpoint should now be paginated ({count, next, previous,
    results} instead of a bare array) and support ?status=/?ordering=."""

    def setUp(self):
        self.company = Company.objects.create(name='Test Shop')
        self.owner_role = Role.objects.create(name='Owner', level=1)
        self.owner = User.objects.create_user(
            email='owner2@test.local', password='x', company=self.company, role=self.owner_role,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        for i in range(30):
            Expense.objects.create(
                company=self.company, category='rent' if i % 2 == 0 else 'utilities',
                amount=10 + i, expense_date=date.today(), description=f'exp-{i}', recorded_by=self.owner,
            )

    def test_list_is_paginated(self):
        r = self.client.get('/api/accounting/expenses/')
        data = r.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 30)
        self.assertEqual(len(data['results']), 25)  # PAGE_SIZE
        self.assertIsNotNone(data['next'])

        r2 = self.client.get(data['next'])
        self.assertEqual(len(r2.json()['results']), 5)

    def test_ordering(self):
        r = self.client.get('/api/accounting/expenses/?ordering=-amount')
        amounts = [float(e['amount']) for e in r.json()['results']]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_category_filter(self):
        r = self.client.get('/api/accounting/expenses/?category=rent')
        results = r.json()['results']
        self.assertTrue(results)
        self.assertTrue(all(e['category'] == 'rent' for e in results))

    def test_invoice_status_filter_and_ordering(self):
        from crm.models import Customer
        from sales.models import Invoice

        customer = Customer.objects.create(company=self.company, name='Test Customer')
        for i, status in enumerate(['draft', 'paid', 'paid', 'overdue']):
            Invoice.objects.create(
                company=self.company, customer=customer, status=status, total=100 + i,
                invoice_date=date.today(), created_by=self.owner,
            )

        r = self.client.get('/api/sales/invoices/?status=paid')
        results = r.json()['results']
        self.assertEqual(len(results), 2)
        self.assertTrue(all(inv['status'] == 'paid' for inv in results))

        r = self.client.get('/api/sales/invoices/?ordering=-total')
        totals = [float(inv['total']) for inv in r.json()['results']]
        self.assertEqual(totals, sorted(totals, reverse=True))
