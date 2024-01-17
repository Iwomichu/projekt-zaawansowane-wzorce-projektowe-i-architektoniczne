import asyncio
from datetime import datetime, timedelta, timezone
from logging import INFO, getLogger
import os
from typing import Callable, NewType
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel, Field


ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
SESSION_REFRESH_INTERVAL_IN_SECONDS = int(
    os.environ.get("SESSION_REFRESH_INTERVAL_IN_SECONDS", "30")
)
SESSION_EXPIRATION_TIME_IN_SECONDS = int(
    os.environ.get("SESSION_EXPIRATION_TIME_IN_SECONDS", "900")
)


ProductId = NewType("ProductId", int)
UserId = NewType("UserId", int)


class CartEntry(BaseModel):
    unit_count: int = 0


class Cart(BaseModel):
    entries_by_product_id: dict[ProductId, CartEntry] = Field(default_factory=dict)
    last_update: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ProductState(BaseModel):
    product_id: ProductId
    total_count: int = 0
    already_put: int = 0


class State(BaseModel):
    cart_by_user_id: dict[UserId, Cart] = dict()
    state_by_product: dict[ProductId, ProductState] = dict()


class ProductNotFoundException(Exception):
    def __init__(self, product_id: int, *args: object) -> None:
        super().__init__(*args)
        self.product_id = product_id


class NotEnoughProductCountAvailableException(Exception):
    def __init__(self, product_id: int, *args: object) -> None:
        super().__init__(*args)
        self.product_id = product_id


class Locks:
    def __init__(self) -> None:
        self.state_lock = asyncio.Lock()
        self.cart_locks: dict[UserId, asyncio.Lock] = dict()
        self.product_locks: dict[ProductId, asyncio.Lock] = dict()


state = State()
locks = Locks()


async def discard_old_session_data():
    logger = getLogger("old-session-discarder")
    logger.setLevel(INFO)
    while True:
        logger.info(
            f"Sleeping for the next {SESSION_REFRESH_INTERVAL_IN_SECONDS} seconds..."
        )
        await asyncio.sleep(SESSION_REFRESH_INTERVAL_IN_SECONDS)
        async with locks.state_lock:
            logger.info(f"Awake!")
            now = datetime.now(tz=timezone.utc)
            oldest_allowed_timestamp = now - timedelta(
                seconds=SESSION_EXPIRATION_TIME_IN_SECONDS
            )
            user_ids_to_discard_session = [
                user_id
                for user_id, cart in state.cart_by_user_id.items()
                if cart.last_update < oldest_allowed_timestamp
            ]
            for user_id in user_ids_to_discard_session:
                logger.info(f"Removing session data for {user_id=}")
                for product_id, cart_entry in state.cart_by_user_id[
                    user_id
                ].entries_by_product_id.items():
                    async with locks.product_locks[product_id]:
                        state.state_by_product[
                            product_id
                        ].already_put -= cart_entry.unit_count
                del state.cart_by_user_id[user_id]
                del locks.cart_locks[user_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(discard_old_session_data())
    yield


app = FastAPI(lifespan=lifespan)


def increment_count(cart_entry: CartEntry, product_state: ProductState):
    if product_state.already_put + 1 > product_state.total_count:
        raise NotEnoughProductCountAvailableException(product_state.product_id)
    else:
        cart_entry.unit_count += 1
        product_state.already_put += 1


def decrement_count(cart_entry: CartEntry, product_state: ProductState):
    cart_entry.unit_count -= 1
    product_state.already_put -= 1


def reset_count(cart_entry: CartEntry, product_state: ProductState):
    product_state.already_put -= cart_entry.unit_count
    cart_entry.unit_count = 0


async def modify_user_cart_entry(
    user_id: UserId,
    product_id: ProductId,
    handler: Callable[[CartEntry, ProductState], None],
):
    async with locks.state_lock:
        if user_id not in state.cart_by_user_id:
            state.cart_by_user_id[user_id] = Cart()
            locks.cart_locks[user_id] = asyncio.Lock()
        if product_id not in state.state_by_product:
            raise ProductNotFoundException(product_id)
    async with locks.cart_locks[user_id], locks.product_locks[product_id]:
        cart = state.cart_by_user_id[user_id]
        cart.last_update = datetime.now(tz=timezone.utc)
        product_state = state.state_by_product[product_id]
        if product_id not in cart.entries_by_product_id:
            cart.entries_by_product_id[product_id] = CartEntry()
        try:
            handler(cart.entries_by_product_id[product_id], product_state)
        except NotEnoughProductCountAvailableException:
            product_state.already_put -= cart.entries_by_product_id[
                product_id
            ].unit_count
            cart.entries_by_product_id[product_id].unit_count = 0
            raise


@app.put("/state", status_code=201)
async def overwrite_state(new_state: State):
    async with locks.state_lock:
        state.cart_by_user_id = new_state.cart_by_user_id
        state.state_by_product = new_state.state_by_product
        locks.cart_locks = {
            user_id: asyncio.Lock() for user_id in new_state.cart_by_user_id
        }
        locks.product_locks = {
            product_id: asyncio.Lock() for product_id in state.state_by_product
        }


@app.get("/products")
async def get_current_product_counts(product_ids: list[ProductId] | None = None):
    if product_ids is None:
        product_ids = list(state.state_by_product.keys())
    return {
        product_id: state.state_by_product[product_id] for product_id in product_ids
    }


@app.get("/cart/{user_id}")
async def get_cart(user_id: UserId):
    return state.cart_by_user_id.get(user_id, Cart())


@app.post("/cart/{user_id}/{product_id}/increment", status_code=200)
async def increment_amount_in_cart(user_id: UserId, product_id: ProductId):
    await modify_user_cart_entry(user_id, product_id, increment_count)


@app.post("/cart/{user_id}/{product_id}/decrement", status_code=200)
async def decrement_amount_in_cart(user_id: UserId, product_id: ProductId):
    await modify_user_cart_entry(user_id, product_id, decrement_count)


@app.post("/cart/{user_id}/{product_id}/reset", status_code=200)
async def reset_amount_in_cart(user_id: UserId, product_id: ProductId):
    await modify_user_cart_entry(user_id, product_id, reset_count)


@app.post("/cart/{user_id}/checkout", status_code=200)
async def checkout_cart(user_id: UserId):
    async with locks.cart_locks[user_id]:
        for product_id, entry in state.cart_by_user_id[
            user_id
        ].entries_by_product_id.items():
            async with locks.product_locks[product_id]:
                product_state = state.state_by_product[product_id]
                difference = product_state.total_count - entry.unit_count
                if difference < 0:
                    reset_count(entry, product_state)
                    raise NotEnoughProductCountAvailableException(
                        product_state.product_id
                    )
                product_state.already_put -= entry.unit_count
                product_state.total_count -= entry.unit_count
        del state.cart_by_user_id[user_id]
    del locks.cart_locks[user_id]


@app.post("/product/{product_id}/reduce")
async def reduce_amount_available(product_id: ProductId, amount: int):
    async with locks.product_locks[product_id]:
        state.state_by_product[product_id].total_count -= amount


@app.post("/product/{product_id}/increase")
async def increase_amount_available(product_id: ProductId, amount: int):
    async with locks.state_lock:
        if product_id not in state.state_by_product:
            state.state_by_product[product_id] = ProductState(product_id=product_id)
            locks.product_locks[product_id] = asyncio.Lock()
    async with locks.product_locks[product_id]:
        state.state_by_product[product_id].total_count += amount
