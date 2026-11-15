from django.contrib.auth import SESSION_KEY
from django.contrib.auth.hashers import check_password, identify_hasher
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    password = "Maple!Orbit73-Cedar"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", email="alice@example.com", password=cls.password
        )

    def registration_data(self, **changes):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": self.password,
            "password2": self.password,
        }
        data.update(changes)
        return data

    def test_home_sends_visitors_to_login(self):
        self.assertRedirects(self.client.get(reverse("home")), reverse("accounts:login"))

    def test_home_sends_signed_in_users_to_dashboard(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse("home")), reverse("accounts:dashboard"))

    def test_registration_saves_user_with_hashed_password(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data())
        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(check_password(self.password, user.password))
        self.assertEqual(identify_hasher(user.password).algorithm, "pbkdf2_sha256")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_registration_success_message_is_visible(self):
        response = self.client.post(
            reverse("accounts:register"), self.registration_data(), follow=True
        )
        self.assertContains(response, "Account created! Sign in with your new credentials.")

    def test_registration_rejects_missing_fields(self):
        response = self.client.post(reverse("accounts:register"), {})
        for field in ("username", "email", "password1", "password2"):
            self.assertFormError(response.context["form"], field, "This field is required.")
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("accounts:register"), self.registration_data(username="alice")
        )
        self.assertFormError(
            response.context["form"], "username", "A user with that username already exists."
        )
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_invalid_email(self):
        response = self.client.post(
            reverse("accounts:register"), self.registration_data(email="not-an-email")
        )
        self.assertFormError(response.context["form"], "email", "Enter a valid email address.")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("accounts:register"), self.registration_data(password2="Different!Pass42")
        )
        self.assertFormError(
            response.context["form"], "password2", "The two password fields didn’t match."
        )
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_registration_rejects_weak_passwords(self):
        for password in ("abc", "12345678901", "password", "newuser"):
            with self.subTest(password=password):
                response = self.client.post(
                    reverse("accounts:register"),
                    self.registration_data(password1=password, password2=password),
                )
                self.assertTrue(response.context["form"].errors.get("password2"))
                self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_registration_rejects_invalid_username(self):
        response = self.client.post(
            reverse("accounts:register"), self.registration_data(username="has spaces")
        )
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_login_creates_authenticated_session(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "alice", "password": self.password}
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "alice", "password": "wrong"}
        )
        self.assertContains(response, "Please enter a correct username and password.")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("accounts:login"), {"username": "alice", "password": self.password}
        )
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_dashboard_redirects_anonymous_users_with_next(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:login") + "?next=/dashboard/")

    def test_dashboard_displays_current_user_details(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "Welcome, <span>alice</span>.")
        self.assertContains(response, "alice@example.com")
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_signed_in_users_redirect_away_from_login_and_registration(self):
        self.client.force_login(self.user)
        for name in ("accounts:login", "accounts:register"):
            with self.subTest(route=name):
                self.assertRedirects(self.client.get(reverse(name)), reverse("accounts:dashboard"))

    def test_login_preserves_safe_next_destination(self):
        response = self.client.get(reverse("accounts:login"), {"next": "/dashboard/"})
        self.assertContains(response, 'name="next" value="/dashboard/"')
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "alice", "password": self.password, "next": "/dashboard/?from=login"},
        )
        self.assertRedirects(response, "/dashboard/?from=login")

    def test_login_rejects_external_next_destination(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "alice", "password": self.password, "next": "https://example.com/"},
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_logout_clears_session_and_protects_dashboard_again(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertRedirects(
            self.client.get(reverse("accounts:dashboard")),
            reverse("accounts:login") + "?next=/dashboard/",
        )

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)

    def test_csrf_rejects_all_post_forms_without_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for name in ("accounts:register", "accounts:login", "accounts:logout"):
            with self.subTest(route=name):
                self.assertEqual(client.post(reverse(name), {}).status_code, 403)

    def test_complete_flow_with_csrf_and_persisted_session(self):
        """Exercise actual forms, CSRF rotation, database writes, and logout."""
        client = Client(enforce_csrf_checks=True)
        response = client.get(reverse("accounts:register"))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        response = client.post(
            reverse("accounts:register"),
            self.registration_data(csrfmiddlewaretoken=client.cookies["csrftoken"].value),
        )
        self.assertRedirects(response, reverse("accounts:login"))
        client.get(reverse("accounts:login"))
        response = client.post(
            reverse("accounts:login"),
            {
                "username": "newuser",
                "password": self.password,
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            },
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))

        # A new client with the same cookies restores authentication from SQLite.
        returning_client = Client(enforce_csrf_checks=True)
        returning_client.cookies = client.cookies.copy()
        self.assertContains(
            returning_client.get(reverse("accounts:dashboard")), "newuser@example.com"
        )
        response = returning_client.post(
            reverse("accounts:logout"),
            {"csrfmiddlewaretoken": returning_client.cookies["csrftoken"].value},
        )
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn(SESSION_KEY, returning_client.session)
        self.assertEqual(returning_client.get(reverse("accounts:dashboard")).status_code, 302)
