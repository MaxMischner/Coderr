from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from markt_coderr.models import Offer, OfferDetail, Order, Profile, Review


class Command(BaseCommand):
	help = "Seed demo data for Coderr"

	def handle(self, *args, **options):
		User = get_user_model()

		users_data = [
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

		created_users = []
		for data in users_data:
			user, created = User.objects.get_or_create(
				username=data["username"],
				defaults={
					"email": data["email"],
					"first_name": data["first_name"],
					"last_name": data["last_name"],
				},
			)
			if created:
				user.set_password(data["password"])
				user.save()
			created_users.append(user)
			Profile.objects.update_or_create(
				user=user,
				defaults={
					"type": data["type"],
					"location": "Berlin",
					"tel": "123456789",
					"description": "Demo description",
					"working_hours": "9-17",
				},
			)

		business_users = [u for u in created_users if u.profile.type == Profile.TYPE_BUSINESS]
		customer_users = [u for u in created_users if u.profile.type == Profile.TYPE_CUSTOMER]

		offers_specs = [
			{
				"title": "Website Design",
				"description": "Professionelles Website-Design.",
			},
			{
				"title": "Logo Design",
				"description": "Individuelle Logos für Unternehmen.",
			},
		]

		offers = []
		for idx, spec in enumerate(offers_specs):
			owner = business_users[idx % len(business_users)]
			offer, _ = Offer.objects.get_or_create(
				user=owner,
				title=spec["title"],
				defaults={
					"description": spec["description"],
					"image": None,
				},
			)
			offers.append(offer)
			self._ensure_offer_details(offer)

		# Reviews
		for business in business_users:
			for customer in customer_users:
				Review.objects.get_or_create(
					business_user=business,
					reviewer=customer,
					defaults={"rating": 5, "description": "Top Qualität!"},
				)

		# Orders
		for offer in offers:
			detail = offer.details.first()
			if detail:
				Order.objects.get_or_create(
					customer_user=customer_users[0],
					business_user=offer.user,
					defaults={
						"title": detail.title,
						"revisions": detail.revisions,
						"delivery_time_in_days": detail.delivery_time_in_days,
						"price": detail.price,
						"features": detail.features,
						"offer_type": detail.offer_type,
					},
				)

		self.stdout.write(self.style.SUCCESS("Demo data seeded."))

	def _ensure_offer_details(self, offer):
		default_details = [
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

		for detail in default_details:
			OfferDetail.objects.get_or_create(
				offer=offer,
				offer_type=detail["offer_type"],
				defaults=detail,
			)