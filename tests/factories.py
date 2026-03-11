import uuid

import factory
from faker import Faker

from smm.models.post_target import PostTargetStatus
from smm.models.social_account import Platform
from smm.services.auth import hash_password

fake = Faker()


class UserFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.LazyFunction(fake.email)
    hashed_password = factory.LazyFunction(lambda: hash_password("testpassword123"))


class SocialAccountFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    platform = Platform.FACEBOOK
    platform_user_id = factory.LazyFunction(lambda: str(fake.random_int()))
    access_token = factory.LazyFunction(lambda: fake.sha256())
    refresh_token = None
    token_expires_at = None


class PostFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    primary_link = None
    image_url = None
    scheduled_at = None


class PostTargetFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    post_id = factory.LazyFunction(uuid.uuid4)
    social_account_id = factory.LazyFunction(uuid.uuid4)
    status = PostTargetStatus.DRAFT
    published_at = None
    platform_post_id = None
    error_message = None
