import base64

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.core.management.base import BaseCommand
from py_vapid import Vapid


def base64url_encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("ascii")


class Command(BaseCommand):
    help = "Generate VAPID keys for browser push notifications."

    def handle(self, *args, **options):
        vapid = Vapid()
        vapid.generate_keys()

        private_number = vapid.private_key.private_numbers().private_value
        private_key = base64url_encode(private_number.to_bytes(32, "big"))
        public_key = base64url_encode(
            vapid.public_key.public_bytes(
                Encoding.X962,
                PublicFormat.UncompressedPoint,
            )
        )

        self.stdout.write("Add these values to your .env file:")
        self.stdout.write("")
        self.stdout.write(f"VAPID_PUBLIC_KEY={public_key}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private_key}")
        self.stdout.write("VAPID_ADMIN_EMAIL=team13web@gmail.com")
