from sqlmodel import Session, SQLModel, create_engine

from app.services import audit_log_service, auth_admin_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_create_role_user_and_audit_logs():
    with _make_session() as session:
        permission = auth_admin_service.create_permission(session, type('obj', (), {
            'code': 'purchase.view', 'name': '查看采购', 'resource': 'purchase', 'action': 'view'
        }))
        role = auth_admin_service.create_role(session, type('obj', (), {
            'code': 'manager', 'name': '经理', 'permission_ids': [permission.id]
        }))
        user = auth_admin_service.create_user(session, type('obj', (), {
            'username': 'admin', 'display_name': '管理员', 'password': 'secret123', 'role_ids': [role['id']], 'is_superuser': True
        }))

        assert user['username'] == 'admin'
        assert role['permission_codes'] == ['purchase.view']
        logs = audit_log_service.list_logs(session)
        assert len(logs) >= 3



def test_ensure_dev_admin_creates_bootstrap_user_when_empty():
    with _make_session() as session:
        user = auth_admin_service.ensure_dev_admin(session)
        assert user is not None
        assert user.username == 'admin'
        assert user.is_superuser is True

        same_user = auth_admin_service.ensure_dev_admin(session)
        assert same_user.id == user.id
