"""Atomic content creation. No external storage calls inside the database transaction."""

import math

from sqlalchemy.orm import Session

from tomateto.business.content.contracts import (
    PostInput,
    TimeSource,
    WritePolicy,
    invalid,
    validate_bigint,
)
from tomateto.dataaccess.content.dish_repo import DishRepository
from tomateto.dataaccess.content.media_upload_repo import MediaUploadRepository, UploadRejectedError
from tomateto.dataaccess.content.post_projection import PostProjection
from tomateto.dataaccess.content.post_repo import PostRepository
from tomateto.dataaccess.content.restaurant_repo import RestaurantRepository
from tomateto.domain.content.normalization import normalize_name
from tomateto.domain.content.records import PostImageRecord, PostRecord
from tomateto.shared.identity import Principal
from tomateto.shared.transaction import TransactionManager


def validate_input(value: PostInput, *, creating: bool) -> None:
    if creating and value.dish_name is None:
        raise invalid("dishName", "REQUIRED_FIELD")
    if value.dish_name is not None:
        try:
            normalize_name(value.dish_name)
        except ValueError:
            raise invalid("dishName", "REQUIRED_FIELD") from None
    if value.restaurant_id is not None:
        validate_bigint(value.restaurant_id, "restaurantId")
    for field, number, limit in [
        ("latitude", value.latitude, 90),
        ("longitude", value.longitude, 180),
    ]:
        if number is not None and (not math.isfinite(number) or abs(number) > limit):
            raise invalid(field, "LOCATION_INVALID")
    if (value.latitude is None) != (value.longitude is None):
        raise invalid("latitude", "LOCATION_INVALID")
    if value.images is not None:
        if len(value.images) > 5:
            raise invalid("images", "IMAGE_LIMIT")
        positions, tickets, existing = set(), set(), set()
        for image in value.images:
            if type(image.position) is not int or image.position < 0 or image.position in positions:
                raise invalid("images", "POSITION_INVALID")
            positions.add(image.position)
            if (image.image_id is None) == (image.upload_id is None):
                raise invalid("images", "IMAGE_REFERENCE_INVALID")
            if image.image_id is not None:
                if creating or image.image_id in existing:
                    raise invalid("images", "IMAGE_REFERENCE_INVALID")
                existing.add(image.image_id)
            if image.upload_id is not None:
                if image.upload_id in tickets:
                    raise invalid("images", "IMAGE_REFERENCE_INVALID")
                tickets.add(image.upload_id)


class PostLifecycleService:
    def __init__(self, session: Session, policy: WritePolicy, clock: TimeSource) -> None:
        self.session, self.policy, self.clock = session, policy, clock

    def resolve_restaurant(self, value: PostInput) -> int | None:
        repo = RestaurantRepository(self.session)
        if value.restaurant_id is not None:
            if repo.find_by_id(value.restaurant_id) is None:
                raise invalid("restaurantId", "RESOURCE_MISSING")
            return value.restaurant_id
        if value.restaurant_name and value.restaurant_name.strip():
            # User decision: no guessed deduplication, even within 100 metres.
            return repo.create(
                value.restaurant_name,
                value.address,
                latitude=value.latitude,
                longitude=value.longitude,
            ).id
        return None

    def create_post(self, principal: Principal | None, value: PostInput) -> PostRecord:
        owner = self.policy.authorize_write(principal, "createPost")
        validate_input(value, creating=True)

        def write() -> PostRecord:
            if value.dish_name is None:
                raise invalid("dishName", "REQUIRED_FIELD")
            dish = DishRepository(self.session).upsert(value.dish_name)
            restaurant_id = self.resolve_restaurant(value)
            now = self.clock.now()
            projection = PostProjection(self.session)
            post_id = projection.allocate_id("posts")
            record = PostRecord(
                id=post_id,
                user_id=owner,
                dish_id=dish.id,
                restaurant_id=restaurant_id,
                caption=value.caption or None,
                feeling=value.feeling or None,
                location_name=value.restaurant_name or None,
                location_address=value.address or None,
                latitude=value.latitude,
                longitude=value.longitude,
                price_range=value.price_range,
                recipe_ingredients=(value.recipe.ingredients or []) if value.recipe else [],
                recipe_steps=(value.recipe.instructions or []) if value.recipe else [],
                is_hidden=False,
                created_at=now,
                updated_at=now,
            )
            saved = PostRepository(self.session).save(record)
            images = []
            for index, item in enumerate(value.images or []):
                if item.upload_id is None:
                    raise invalid(f"images.{index}", "IMAGE_REFERENCE_INVALID")
                try:
                    asset = MediaUploadRepository(self.session).consume(
                        item.upload_id, owner, "POST", now
                    )
                except UploadRejectedError:
                    raise invalid(f"images.{index}", "UPLOAD_INVALID") from None
                images.append(
                    PostImageRecord(
                        projection.allocate_id("post_images"), post_id, asset.id, item.position
                    )
                )
            PostRepository(self.session).replace_images(post_id, images)
            return saved

        return TransactionManager(self.session).run(write)
