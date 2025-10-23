from .extension import ma

class UserSchema(ma.Schema):
    class Meta:
        fields = ("uuid", "username", "phone", "email", "date_of_birth", "location", "google_id", "provider")