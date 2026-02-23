from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from course.models import Course, Category
from accounts.models import InstructorProfile
from result.models import Enrollment
from payments.models import Order
from unittest.mock import patch

User = get_user_model()

class CheckoutTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.student = User.objects.create_user(
            username='student', email='student@test.com', password='password'
        )
        self.instructor_user = User.objects.create_user(
            username='instructor', email='inst@test.com', password='password', is_instructor=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        # Setup Instructor
        InstructorProfile.objects.get_or_create(user=self.instructor_user)
        
        # Setup Category
        self.category = Category.objects.create(name="Tech", slug="tech")
        
        # Create Courses
        self.course_paid = Course.objects.create(
            title="Paid Course",
            slug="paid-course",
            price=100.00,
            instructor=self.instructor_user,
            category=self.category,
            status='published'
        )
        self.course_free = Course.objects.create(
            title="Free Course",
            slug="free-course",
            price=0.00,
            instructor=self.instructor_user,
            category=self.category,
            status='published'
        )
        
    def test_checkout_price_integrity(self):
        """
        Ensure backend ignores any price sent by frontend (if we were sending it)
        and uses DB price.
        """
        # We don't verify frontend price payload because our API doesn't even accept it.
        # But we ensure the created Order has the correct price.
        
        with patch('stripe.checkout.Session.create') as mock_stripe:
            from unittest.mock import Mock
            session_mock = Mock()
            session_mock.id = 'sess_123'
            session_mock.url = 'http://test.com'
            mock_stripe.return_value = session_mock
            
            payload = {
                'course_ids': [self.course_paid.id]
            }
            response = self.client.post('/api/payments/checkout/', payload, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(Order.objects.exists())
            order = Order.objects.first()
            self.assertEqual(float(order.total_amount), 100.00)

    def test_already_enrolled_prevention(self):
        """
        Should fail if purchasing an already enrolled course
        """
        # Enroll first
        Enrollment.objects.create(student=self.student, course=self.course_paid)
        
        payload = {'course_ids': [self.course_paid.id]}
        response = self.client.post('/api/payments/checkout/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", response.data['error'])

    def test_empty_cart(self):
        payload = {'course_ids': []}
        response = self.client.post('/api/payments/checkout/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_course_id(self):
        payload = {'course_ids': [99999]} # Non-existent
        response = self.client.post('/api/payments/checkout/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_free_course_checkout(self):
        """
        Free courses should bypass Stripe and enroll immediately
        """
        payload = {'course_ids': [self.course_free.id]}
        response = self.client.post('/api/payments/checkout/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['free'])
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course_free).exists())
