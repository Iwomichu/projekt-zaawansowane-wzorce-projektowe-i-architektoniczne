from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy import Numeric, Select, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from zwpa.model import (
    ClientRequest,
    Product,
    Supply,
    SupplyOffer,
    SupplyReceipt,
    SupplyStatus,
    UserRole,
    WarehouseProduct,
)

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker


@dataclass
class FullProductView:
    id: int
    label: str
    unit: str
    retail_price: Decimal
    mean_sell_bulk_price: Decimal
    mean_buy_bulk_price: Decimal
    amount_in_our_warehouses: int
    amount_incoming_to_our_warehouses: int
    amount_requested_by_us: int
    amount_requested_by_clients: int


class ListProductsWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def list_products(self, user_id: int) -> list[FullProductView]:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)

        with self.session_maker() as session:
            query = build_full_product_view_query().order_by(Product.id)
            return [FullProductView(*record) for record in session.execute(query)]


def build_full_product_view_query() -> Select:
    mean_sell_bulk_price_query = __mean_sell_bulk_price_query()
    mean_buy_bulk_price_query = __mean_buy_bulk_price_query()
    amount_in_our_warehouses_query = __amount_in_our_warehouses_query()
    amount_incoming_to_our_warehouses_query = (
        __amount_incoming_to_our_warehouses_query()
    )
    amount_requested_by_us_query = __amount_requested_by_us_query()
    amount_requested_by_clients_query = __amount_requested_by_clients_query()
    return (
        select(
            Product.id,
            Product.label,
            Product.unit,
            Product.retail_price,
            func.coalesce(mean_sell_bulk_price_query.c.mean_price, 0.0),
            func.coalesce(mean_buy_bulk_price_query.c.mean_price, 0.0),
            func.coalesce(amount_in_our_warehouses_query.c.amount, 0),
            func.coalesce(amount_incoming_to_our_warehouses_query.c.amount, 0),
            func.coalesce(amount_requested_by_us_query.c.amount, 0),
            func.coalesce(amount_requested_by_clients_query.c.amount, 0),
        )
        .join(
            mean_sell_bulk_price_query,
            Product.id == mean_sell_bulk_price_query.c.product_id,
            isouter=True,
        )
        .join(
            mean_buy_bulk_price_query,
            Product.id == mean_buy_bulk_price_query.c.product_id,
            isouter=True,
        )
        .join(
            amount_in_our_warehouses_query,
            Product.id == amount_in_our_warehouses_query.c.product_id,
            isouter=True,
        )
        .join(
            amount_incoming_to_our_warehouses_query,
            Product.id == amount_incoming_to_our_warehouses_query.c.product_id,
            isouter=True,
        )
        .join(
            amount_requested_by_us_query,
            Product.id == amount_requested_by_us_query.c.product_id,
            isouter=True,
        )
        .join(
            amount_requested_by_clients_query,
            Product.id == amount_requested_by_clients_query.c.product_id,
            isouter=True,
        )
    )


def __mean_sell_bulk_price_query():
    return (
        select(
            ClientRequest.product_id,
            func.avg(ClientRequest.price.cast(Numeric)).label("mean_price"),
        )
        .where(ClientRequest.accepted == True)
        .group_by(ClientRequest.product_id)
        .subquery()
    )


def __mean_buy_bulk_price_query():
    return (
        select(
            Supply.product_id,
            func.avg(SupplyOffer.price.cast(Numeric)).label("mean_price"),
        )
        .join(SupplyOffer)
        .join(SupplyReceipt)
        .group_by(Supply.product_id)
        .subquery()
    )


def __amount_in_our_warehouses_query():
    return (
        select(
            WarehouseProduct.product_id,
            func.sum(WarehouseProduct.current_count).label("amount"),
        )
        .group_by(WarehouseProduct.product_id)
        .subquery()
    )


def __amount_incoming_to_our_warehouses_query():
    return (
        select(Supply.product_id, func.sum(Supply.unit_count).label("amount"))
        .where(Supply.status == SupplyStatus.OFFER_ACCEPTED)
        .group_by(Supply.product_id)
        .subquery()
    )


def __amount_requested_by_us_query():
    return (
        select(Supply.product_id, func.sum(Supply.unit_count).label("amount"))
        .where(Supply.status == SupplyStatus.REQUESTED)
        .group_by(Supply.product_id)
        .subquery()
    )


def __amount_requested_by_clients_query():
    return (
        select(
            ClientRequest.product_id,
            func.sum(ClientRequest.unit_count).label("amount"),
        )
        .where(ClientRequest.accepted == False)
        .group_by(ClientRequest.product_id)
        .subquery()
    )
