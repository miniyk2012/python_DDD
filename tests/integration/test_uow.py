import pytest
from allocation.domain import model
from allocation.domain.model import Batch
from allocation.service_layer import unit_of_work
from tests.unit.test_services import FakeRepository


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id"
        " WHERE orderline_id=:orderlineid",
        dict(orderlineid=orderlineid),
    )
    return batchref


def test_uow_can_retrieve_a_batch_and_allocate_to_it(fake_session_factory):
    """写一个依赖于fake_session和fake_repository的UoW用例, 这个用例只是个例子, 违反了DON’T MOCK WHAT YOU DON’T OWN原则"""
    uow = unit_of_work.SqlAlchemyUnitOfWork(fake_session_factory)
    with uow:
        uow.batches = FakeRepository([Batch("batch1", "HIPSTER-WORKBENCH", 100, None)])
        batch = uow.batches.get(reference="batch1")
        assert batch.available_quantity == 100
        assert not uow.session.committed
        line = model.OrderLine("o1", "HIPSTER-WORKBENCH", 10)
        batch.allocate(line)
        uow.commit()
    assert uow.session.committed
    the_batch = uow.batches.get("batch1")
    assert the_batch.reference == "batch1"
    assert the_batch.available_quantity == 90


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)
        # 没有commit
    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, "batch1", "LARGE-FORK", 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []
