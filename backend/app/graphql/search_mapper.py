"""Map search data already loaded by the service to GraphQL."""

import strawberry

from app.graphql.search import SearchConnection, SearchEdge, SearchResult, SearchType
from app.graphql.types import (
    Cursor,
    Dish,
    PageInfo,
    Post,
    PostImage,
    PriceRange,
    Recipe,
    Restaurant,
    User,
)
from app.services.discovery_search import SearchPage


def map_search(page: SearchPage) -> SearchConnection:
    result, details = page.result, page.details
    restaurant_by_id = {
        row["id"]: Restaurant(
            id=strawberry.ID(str(row["id"])),
            name=row["name"],
            address=row["address"],
            latitude=row["latitude"],
            longitude=row["longitude"],
        )
        for row in details.restaurants
    }
    images_by_post: dict[int, list[PostImage]] = {}
    for row in details.images:
        images_by_post.setdefault(row["post_id"], []).append(
            PostImage(id=strawberry.ID(str(row["id"])), url=row["url"], position=row["position"])
        )
    post_by_id: dict[int, Post] = {}
    for row in details.posts:
        restaurant = None
        if row["restaurant_id"] is not None and row["restaurant_name"] is not None:
            restaurant = Restaurant(
                id=strawberry.ID(str(row["restaurant_id"])),
                name=row["restaurant_name"],
                address=row["restaurant_address"],
                latitude=row["restaurant_latitude"],
                longitude=row["restaurant_longitude"],
            )
        name_visible = (
            details.viewer_id == row["user_id"] or "displayName" in row["public_profile_fields"]
        )
        author = User(
            id=strawberry.ID(str(row["user_id"])),
            display_name=row["display_name"] if name_visible else "Người dùng",
            avatar_url=None,
        )
        post_by_id[row["id"]] = Post(
            id=strawberry.ID(str(row["id"])),
            dish_name=row["dish_name"],
            caption=row["caption"],
            images=images_by_post.get(row["id"], []),
            author=author,
            price_range=PriceRange(row["price_range"]) if row["price_range"] else None,
            address=row["location_address"],
            restaurant=restaurant,
            recipe=Recipe(ingredients=row["recipe_ingredients"], instructions=row["recipe_steps"]),
            feeling=row["feeling"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            like_count=row["like_count"],
            is_liked_by_viewer=row["is_liked"],
            is_saved_by_viewer=row["is_saved"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    edges: list[SearchEdge] = []
    for edge in result.edges:
        hit = edge.node
        kind = SearchType(hit.kind)
        if kind is SearchType.DISH:
            node = SearchResult(
                type=kind, dish=Dish(id=strawberry.ID(str(hit.item_id)), name=hit.title)
            )
        elif kind is SearchType.RESTAURANT:
            restaurant = restaurant_by_id.get(hit.item_id)
            if restaurant is None:
                continue
            node = SearchResult(type=kind, restaurant=restaurant)
        else:
            post = post_by_id.get(hit.item_id)
            if post is None:
                continue
            node = SearchResult(type=kind, post=post)
        edges.append(SearchEdge(cursor=Cursor(edge.cursor), node=node))
    return SearchConnection(
        edges=edges,
        page_info=PageInfo(
            end_cursor=Cursor(edges[-1].cursor) if edges else None, has_next_page=result.has_next
        ),
    )
