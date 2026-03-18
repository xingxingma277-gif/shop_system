from sqlmodel import Session, SQLModel, create_engine

from app.services import auth_admin_service, auth_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_authenticate_and_current_user_permissions():
    with _make_session() as session:
        p1 = auth_admin_service.create_permission(session, type('obj', (), {'code': 'admin.user.manage', 'name': '用户管理', 'resource': 'admin', 'action': 'user_manage'}))
        p2 = auth_admin_service.create_permission(session, type('obj', (), {'code': 'audit.view', 'name': '审计查看', 'resource': 'audit', 'action': 'view'}))
        role = auth_admin_service.create_role(session, type('obj', (), {'code': 'admin', 'name': '管理员', 'permission_ids': [p1.id, p2.id]}))
        auth_admin_service.create_user(session, type('obj', (), {'username': 'admin', 'display_name': '管理员', 'password': 'secret123', 'role_ids': [role['id']], 'is_superuser': False}))

        current = auth_service.authenticate(session, 'admin', 'secret123')
        assert current['username'] == 'admin'
        assert 'admin.user.manage' in current['permission_codes']
        assert 'audit.view' in current['permission_codes']
