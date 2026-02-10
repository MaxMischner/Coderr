"""Management command to seed demo data."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from markt_coderr.models import Offer, OfferDetail, Order, Profile, Review


USERS_DATA = [
    {
        "username": "andrey",
        "email": "andrey@example.com",
        "password": "asdasd",
        "first_name": "Andrey",
        "last_name": "Customer",
        "type": Profile.TYPE_CUSTOMER,
    },
    {
        "username": "customer_jane",
        "email": "customer_jane@example.com",
        "password": "asdasd",
        "first_name": "Jane",
        "last_name": "Doe",
        "type": Profile.TYPE_CUSTOMER,
    },
    {
        "username": "kevin",
        "email": "kevin@business.de",
        "password": "asdasd24",
        "first_name": "Kevin",
        "last_name": "Business",
        "type": Profile.TYPE_BUSINESS,
    },
    {
        "username": "biz_maria",
        "email": "maria@business.de",
        "password": "asdasd24",
        "first_name": "Maria",
        "last_name": "Business",
        "type": Profile.TYPE_BUSINESS,
    },
]


OFFER_SPECS = [
    {
        "title": "Website Design",
        "description": "Professionelles Website-Design.",
    },
    {
        "title": "Logo Design",
        "description": "Individuelle Logos für Unternehmen.",
    },
]


OFFER_DETAILS = [
    {
        "offer_type": OfferDetail.OFFER_TYPE_BASIC,
        "title": "Basic Design",
        "revisions": 2,
        "delivery_time_in_days": 5,
        "price": 100,
        "features": ["Logo Design", "Visitenkarte"],
    },
    {
        "offer_type": OfferDetail.OFFER_TYPE_STANDARD,
        "title": "Standard Design",
        "revisions": 5,
        "delivery_time_in_days": 7,
        "price": 200,
        "features": ["Logo Design", "Visitenkarte", "Briefpapier"],
    },
    {
        "offer_type": OfferDetail.OFFER_TYPE_PREMIUM,
        "title": "Premium Design",
        "revisions": 10,
        "delivery_time_in_days": 10,
        "price": 500,
        "features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
    },
]


def _order_defaults(detail):
    """Build defaults payload for an order from a detail."""
    return {
        "title": detail.title,
        "revisions": detail.revisions,
        "delivery_time_in_days": detail.delivery_time_in_days,
        "price": detail.price,
        "features": detail.features,
        "offer_type": detail.offer_type,
    }


class Command(BaseCommand):
    """Seed demo data for local development."""
    help = "Seed demo data for Coderr"

    def handle(self, *args, **options):
        """Entry point for the management command."""
        user_model = get_user_model()
        users = self._create_users(user_model)
        business_users, customer_users = self._split_users(users)
        offers = self._create_offers(business_users)
        self._create_reviews(business_users, customer_users)
        self._create_orders(offers, customer_users)
        self.stdout.write(self.style.SUCCESS("Demo data seeded."))

    def _create_users(self, user_model):
        """Create users and profiles from seed data."""
        users = []
        for data in USERS_DATA:
            user = self._get_or_create_user(user_model, data)
            self._update_profile(user, data["type"])
            users.append(user)
        return users

    def _get_or_create_user(self, user_model, data):
        """Get or create a user from seed data."""
        user, created = user_model.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": data["email"], "first_name": data["first_name"], "last_name": data["last_name"]},
        )
        if created:
            user.set_password(data["password"])
            user.save()
        return user

    def _update_profile(self, user, profile_type):
        """Create or update profile details for a user."""
        Profile.objects.update_or_create(
            user=user,
            defaults={
                "type": profile_type,
                "location": "Berlin",
                "tel": "123456789",
                "description": "Demo description",
                "working_hours": "9-17",
            },
        )

    def _split_users(self, users):
        """Split users into business and customer groups."""
        business = [u for u in users if u.profile.type ==
                    Profile.TYPE_BUSINESS]
        customer = [u for u in users if u.profile.type ==
                    Profile.TYPE_CUSTOMER]
        return business, customer

    def _create_offers(self, business_users):
        """Create offers for business users."""
        offers = []
        for idx, spec in enumerate(OFFER_SPECS):
            owner = business_users[idx % len(business_users)]
            offer = self._get_or_create_offer(owner, spec)
            offers.append(offer)
            self._ensure_offer_details(offer)
        return offers

    def _get_or_create_offer(self, owner, spec):
        """Get or create an offer for a business user."""
        offer, _ = Offer.objects.get_or_create(
            user=owner,
            title=spec["title"],
            defaults={"description": spec["description"], "image": None},
        )
        return offer

    def _create_reviews(self, business_users, customer_users):
        """Create reviews for each business and customer pair."""
        for business in business_users:
            for customer in customer_users:
                Review.objects.get_or_create(
                    business_user=business,
                    reviewer=customer,
                    defaults={"rating": 5, "description": "Top Qualität!"},
                )

    def _create_orders(self, offers, customer_users):
        """Create orders for the first customer user."""
        customer = customer_users[0]
        for offer in offers:
            detail = offer.details.first()
            if detail:
                self._get_or_create_order(customer, offer, detail)

    def _get_or_create_order(self, customer, offer, detail):
        """Get or create an order for a detail."""
        Order.objects.get_or_create(
            customer_user=customer,
            business_user=offer.user,
            defaults=_order_defaults(detail),
        )

    def _ensure_offer_details(self, offer):
        """Ensure all offer detail records exist."""
        for detail in OFFER_DETAILS:
            OfferDetail.objects.get_or_create(
                offer=offer,
                offer_type=detail["offer_type"],
                defaults=detail,
            )
