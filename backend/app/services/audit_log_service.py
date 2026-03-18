from sqlmodel import Session, select

from app.models import AuditLog


def record(session: Session, *, action: str, resource_type: str, resource_id: int | None = None,
           detail: str | None = None, actor_user_id: int | None = None, actor_name: str = 'system') -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        actor_name=actor_name,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )
    session.add(log)
    session.flush()
    return log


def list_logs(session: Session, resource_type: str | None = None, action: str | None = None, actor_name: str | None = None):
    stmt = select(AuditLog)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_name:
        stmt = stmt.where(AuditLog.actor_name == actor_name)
    return session.exec(stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())).all()
