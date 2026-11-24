"""T01–T04 integration tests run against the original DOC 6.4-B PostgreSQL DDL."""

import secrets
from datetime import timedelta
from uuid import uuid4

import pytest
from app._stubs.clock import FixedClock
from app._stubs.errors import AuthorizationError
from app.bootstrap.identity_scope import build_identity_service
from app.business.identity.config import IdentityConfig
from app.business.identity.session_token_service import SessionTokenService
from app.dataaccess.identity.account_repository import AccountRepository
from app.dataaccess.identity.device_repository import DeviceRepository
from app.dataaccess.identity.password_reset_repository import PasswordResetRepository
from app.dataaccess.identity.session_repository import SessionRepository
from app.domain.identity.password_reset import PasswordReset
from app.domain.identity.revoked_token import RevokedToken
from app.domain.identity.user import User
from app.domain.identity.user_device import UserDevice
from sqlalchemy import Connection, Engine, event, func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from tests.support.factories import insert_user


def user_record(email: str | None = None) -> User:
    resolved = email or f"{uuid4().hex}@example.invalid"
    return User(
        email=resolved,
        email_normalized=resolved.strip().casefold(),
        password_hash=secrets.token_hex(32),
        display_name="Người kiểm thử",
    )


def new_request(user_id: int, clock: FixedClock) -> PasswordReset:
    return PasswordReset(
        user_id=user_id,
        otp_hash="fixture-otp-hash",
        failed_attempts=0,
        created_at=clock.now(),
        otp_expires_at=clock.now() + timedelta(minutes=10),
    )


def test_tc_be_0107_account_defaults_and_lookup(db_session: Session) -> None:
    repo = AccountRepository(db_session)
    user = user_record("Minh@Example.invalid")
    repo.save(user)
    assert user.token_version == 0 and user.is_active
    assert user.social_links == {} and user.public_profile_fields == []
    assert repo.find_by_email(" MINH@example.invalid ") is user
    assert repo.find_by_id(user.id, for_update=True) is user
    assert repo.find_by_id(-123456) is None
    assert repo.get_token_version(-123456) is None
    repo.update_password(user.id, secrets.token_hex())
    assert repo.bump_token_version(user.id) == 1
    assert repo.get_token_version(user.id) == 1


def test_tc_be_0107_duplicate_normalized_email(db_session: Session) -> None:
    repo = AccountRepository(db_session)
    repo.save(user_record("same@example.invalid"))
    with db_session.begin_nested(), pytest.raises(IntegrityError):
        repo.save(user_record("SAME@example.invalid"))


def test_account_blank_display_name_check(db_session: Session) -> None:
    user = user_record()
    user.display_name = "   "
    with db_session.begin_nested(), pytest.raises(IntegrityError):
        AccountRepository(db_session).save(user)


def test_tc_be_0307_one_open_request(db_session: Session, clock: FixedClock) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = PasswordResetRepository(db_session)
    repo.create(new_request(user.id, clock))
    with db_session.begin_nested(), pytest.raises(IntegrityError):
        repo.create(new_request(user.id, clock))


def test_tc_be_0308_latest_and_invalidate(db_session: Session, clock: FixedClock) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = PasswordResetRepository(db_session)
    first = new_request(user.id, clock)
    repo.create(first)
    assert repo.invalidate_open_for_user(user.id, clock.now()) == 1
    db_session.refresh(first)
    second = new_request(user.id, clock)
    repo.create(second)
    assert repo.find_latest_by_email(user.email.upper(), for_update=True) is second
    assert repo.find_latest_by_email("missing@example.invalid") is None
    assert first.invalidated_at == clock.now()


def test_grant_consume_once_and_preserve_live_grant(db_session: Session, clock: FixedClock) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = PasswordResetRepository(db_session)
    request = new_request(user.id, clock)
    request.verified_at = clock.now()
    request.reset_token_hash = secrets.token_hex(32)
    request.reset_expires_at = clock.now() + timedelta(minutes=15)
    repo.create(request)
    after_otp = clock.now() + timedelta(minutes=11)
    assert repo.purge_expired(after_otp) == 0  # OTP expired, but verified grant still live
    assert repo.find_by_grant_hash(request.reset_token_hash) is request
    assert not repo.consume(request.id, "wrong-hash", clock.now())
    assert repo.consume(request.id, request.reset_token_hash, clock.now())
    assert not repo.consume(request.id, request.reset_token_hash, clock.now())


def test_expired_grant_not_consumed(db_session: Session, clock: FixedClock) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = PasswordResetRepository(db_session)
    request = new_request(user.id, clock)
    request.verified_at = clock.now()
    request.reset_token_hash = secrets.token_hex(32)
    request.reset_expires_at = clock.now() + timedelta(minutes=15)
    repo.create(request)
    assert not repo.consume(request.id, request.reset_token_hash, request.reset_expires_at)
    assert repo.purge_expired(request.reset_expires_at) == 1


@pytest.mark.parametrize("field", ["failed_attempts", "grant_fields"])
def test_reset_database_checks(field: str, db_session: Session, clock: FixedClock) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    request = new_request(user.id, clock)
    if field == "failed_attempts":
        request.failed_attempts = 6
    else:
        request.reset_token_hash = secrets.token_hex(32)
    with db_session.begin_nested(), pytest.raises(IntegrityError):
        PasswordResetRepository(db_session).create(request)


def test_tc_be_0407_revoke_idempotent_and_prune(db_session: Session, clock: FixedClock) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = SessionRepository(db_session)
    expired, alive = uuid4(), uuid4()
    repo.revoke(expired, user.id, clock.now())
    repo.revoke(expired, user.id, clock.now())
    repo.revoke(alive, user.id, clock.now() + timedelta(days=1))
    assert db_session.scalar(select(func.count()).select_from(RevokedToken)) == 2
    assert repo.is_revoked(expired) and repo.is_revoked(alive)
    assert repo.prune(clock.now()) == 1
    assert not repo.is_revoked(expired) and repo.is_revoked(alive)


@pytest.mark.parametrize("violation", ["duplicate_token", "bad_platform"])
def test_tc_be_0109_device_checks(violation: str, db_session: Session) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = DeviceRepository(db_session)
    token = secrets.token_hex()
    first = UserDevice(user_id=user.id, push_token=token, platform="web")
    repo.save(first)
    assert repo.list_by_user(user.id) == [first] and first.belongs_to(user.id)
    broken = UserDevice(
        user_id=user.id,
        push_token=token if violation == "duplicate_token" else secrets.token_hex(),
        platform="bad" if violation == "bad_platform" else "android",
    )
    with db_session.begin_nested(), pytest.raises(IntegrityError):
        repo.save(broken)


def test_device_remove_checks_owner(db_session: Session) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    repo = DeviceRepository(db_session)
    token = secrets.token_hex()
    repo.save(UserDevice(user_id=user.id, push_token=token, platform="web"))
    repo.remove(user.id + 100, token)
    assert len(repo.list_by_user(user.id)) == 1
    repo.remove(user.id, token)
    assert repo.list_by_user(user.id) == []


def test_repository_does_not_commit(db_session: Session) -> None:
    with db_session.begin_nested() as transaction:
        user = user_record()
        AccountRepository(db_session).save(user)
        user_id = user.id
        transaction.rollback()
    assert AccountRepository(db_session).find_by_id(user_id) is None


def test_real_verify_detects_revocation_version_and_inactive(
    db_session: Session, identity_config: IdentityConfig, clock: FixedClock
) -> None:
    user = user_record()
    repo = AccountRepository(db_session)
    repo.save(user)
    service = build_identity_service(db_session, identity_config, clock)
    tokens = SessionTokenService(identity_config, clock)
    token = tokens.issue(user)
    assert service.verify_session(token.raw).user_id == user.id
    service.revoke_session(token.raw)
    service.revoke_session(token.raw)
    assert db_session.scalar(select(func.count()).select_from(RevokedToken)) == 1
    with pytest.raises(AuthorizationError):
        service.verify_session(token.raw)
    other = tokens.issue(user)
    repo.bump_token_version(user.id)
    with pytest.raises(AuthorizationError):
        service.verify_session(other.raw)
    refreshed = repo.find_by_id(user.id)
    assert refreshed is not None
    current = tokens.issue(refreshed)
    user.is_active = False
    repo.save(user)
    with pytest.raises(AuthorizationError):
        service.verify_session(current.raw)


def test_tc_be_0308_for_update_really_locks(db_engine: Engine, clock: FixedClock) -> None:
    # Committed fixture is visible to both connections, then deleted in finally.
    with db_engine.begin() as connection:
        user_id = insert_user(connection)
        email = connection.scalar(text("SELECT email FROM users WHERE id=:id"), {"id": user_id})
        repo = PasswordResetRepository(Session(bind=connection))
        repo.create(new_request(user_id, clock))
    try:
        with Session(db_engine) as first, Session(db_engine) as second:
            assert PasswordResetRepository(first).find_latest_by_email(str(email), True) is not None
            second.execute(text("SET LOCAL lock_timeout = '100ms'"))
            with pytest.raises(OperationalError) as error:
                PasswordResetRepository(second).find_latest_by_email(str(email), True)
            assert getattr(error.value.orig, "sqlstate", None) == "55P03"
    finally:
        with db_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM password_resets WHERE user_id=:id"), {"id": user_id}
            )
            connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})


def test_session_rollback_no_rows_leaked(db_connection: Connection) -> None:
    assert db_connection.scalar(text("SELECT count(*) FROM password_resets")) == 0


def test_verified_request_uses_two_selects(
    db_session: Session, identity_config: IdentityConfig, clock: FixedClock
) -> None:
    user = user_record()
    AccountRepository(db_session).save(user)
    token = SessionTokenService(identity_config, clock).issue(user)
    service = build_identity_service(db_session, identity_config, clock)
    statements: list[str] = []

    def record_sql(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    connection = db_session.connection()
    event.listen(connection, "before_cursor_execute", record_sql)
    try:
        service.verify_session(token.raw)
    finally:
        event.remove(connection, "before_cursor_execute", record_sql)
    assert len(statements) == 2
    assert "revoked_tokens" in statements[0] and "users" in statements[1]
