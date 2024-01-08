from dataclasses import dataclass
from sqlalchemy import and_, or_, select
from sqlalchemy.sql.functions import sum as sql_sum
from sqlalchemy.orm import sessionmaker, Session
from zwpa.model import (
    Product,
    Supply,
    SupplyStatus,
    UserRole,
    Warehouse,
    WarehouseProduct,
)

from zwpa.workflows.utils.UserRoleChecker import UserRoleChecker
from zwpa.workflows.warehouse.ListAllWarehousesWorkflow import WarehouseView


@dataclass
class CompleteWarehouseProductView:
    id: int
    label: str
    unit: str
    current_count: int
    incoming_count: int
    already_requested_count: int

    @staticmethod
    def create(
        warehouse_product: WarehouseProduct,
        incoming_count: int | None = None,
        already_requested_count: int | None = None,
    ):
        return CompleteWarehouseProductView(
            id=warehouse_product.id,
            label=warehouse_product.product.label,
            unit=warehouse_product.product.unit,
            current_count=warehouse_product.current_count,
            incoming_count=incoming_count if incoming_count else 0,
            already_requested_count=already_requested_count
            if already_requested_count
            else 0,
        )


@dataclass
class CompleteWarehouseView:
    warehouse: WarehouseView  # TODO: Deduplicate views
    products: list[CompleteWarehouseProductView]


class GetWarehouseDetailsWorkflow:
    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        self.session_maker = session_maker
        self.user_role_checker = UserRoleChecker(self.session_maker)

    def get_warehouse_details(
        self, user_id: int, warehouse_id: int
    ) -> CompleteWarehouseView:
        self.user_role_checker.assert_user_of_role(user_id, role=UserRole.CLERK)
        with self.session_maker() as session:
            warehouse = session.get_one(Warehouse, warehouse_id)
            already_requested_count = (
                select(
                    Product.id,
                    sql_sum(Supply.unit_count).label("already_requested_count"),
                )
                .join(Supply)
                .where(Supply.status == SupplyStatus.REQUESTED)
                .where(Supply.warehouse_id == warehouse_id)
                .group_by(Product.id)
                .subquery("already_requested")
            )
            incoming_count = (
                select(
                    Product.id,
                    sql_sum(Supply.unit_count).label("incoming_count"),
                )
                .join(Supply)
                .where(Supply.status == SupplyStatus.OFFER_ACCEPTED)
                .where(Supply.warehouse_id == warehouse_id)
                .group_by(Product.id)
                .subquery("incoming")
            )
            already_stored_count = (
                select(WarehouseProduct.product_id, WarehouseProduct.current_count)
                .where(WarehouseProduct.warehouse_id == warehouse_id)
                .subquery("current_count")
            )
            query = (
                select(
                    Product,
                    already_stored_count.c.current_count,
                    already_requested_count.c.already_requested_count,
                    incoming_count.c.incoming_count,
                )
                .join(
                    already_stored_count,
                    Product.id == already_stored_count.c.product_id,
                    full=True,
                )
                .join(
                    already_requested_count,
                    Product.id == already_requested_count.c.id,
                    full=True,
                )
                .join(
                    incoming_count,
                    Product.id == incoming_count.c.id,
                    full=True,
                )
                .where(
                    or_(
                        already_stored_count.c.current_count > 0,
                        already_requested_count.c.already_requested_count > 0,
                        incoming_count.c.incoming_count > 0,
                    )
                )
                .order_by(Product.id)
            )
            warehouse_products_with_counts = session.execute(query).all()
            print(query)
            return CompleteWarehouseView(
                warehouse=WarehouseView.create(warehouse),
                products=[
                    CompleteWarehouseProductView(
                        id=product.id,
                        label=product.label,
                        unit=product.unit,
                        current_count=current_count or 0,
                        incoming_count=incoming_count or 0,
                        already_requested_count=already_requested_count or 0,
                    )
                    for product, current_count, already_requested_count, incoming_count in warehouse_products_with_counts
                ],
            )
