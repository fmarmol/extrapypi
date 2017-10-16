from extrapypi.models import User
from extrapypi.extensions import db


def test_ping(client):
    """Test simple ping endpoint"""
    res = client.get('/ping')
    assert b'pong' in res.data


def test_simple(client, db, packages, admin_headers):
    """Test simple view index"""
    res = client.get('/simple/', headers=admin_headers)
    assert b'test-package' in res.data
    assert b'other-package' in res.data


def test_simple_package(client, packages_dirs, releases_dirs, admin_headers):
    """Test simple index for specific package"""
    res = client.get('/simple/test-package/', headers=admin_headers)
    assert b'test-package-0.1' in res.data

    # bad package
    resp = client.get('/simple/bad-package/', headers=admin_headers)
    assert resp.status_code == 404


def test_simple_package_download(client, packages_dirs,
                                 releases_dirs, admin_headers):
    """Test download of a package version"""
    res = client.get(
        '/simple/test-package/test-package-0.1.tar.gz',
        headers=admin_headers
    )
    assert res.status_code == 200
    assert res.data == b'insidepackage'

    # bad package
    resp = client.get(
        '/simple/bad-package/test-package-0.1.tar.gz',
        headers=admin_headers
    )
    assert resp.status_code == 404


def test_list_packages(client, packages, admin_headers):
    """Test list packages dashboard view"""
    res = client.get('/dashboard/', headers=admin_headers)
    assert res.status_code == 200
    assert b'test-package' in res.data
    assert b'other-package' in res.data


def test_search_packages(client, packages, admin_headers):
    """Test search packages"""
    res = client.post('/dashboard/search/', data={"search": "other"})
    assert res.status_code == 200
    assert b'other-package' in res.data
    assert b'test-package' not in res.data


def test_package_details(client, packages, releases):
    """Test view for package details"""
    res = client.get('/dashboard/test-package/')
    assert res.status_code == 200
    assert b'test' in res.data
    assert b'0.1' in res.data
    assert b'test,other' in res.data
    assert b'badmd5' in res.data

    # bad package
    res = client.get('/dashboard/bad-package/')
    assert res.status_code == 404


def test_release_details(client, packages, releases):
    """Test view for release details"""
    res = client.get('/dashboard/test-package/1/')
    assert res.status_code == 200
    assert b'test' in res.data
    assert b'0.1' in res.data
    assert b'test,other' in res.data
    assert b'badmd5' in res.data

    # bad release
    res = client.get('/dashboard/test-package/99/')
    assert res.status_code == 404


def test_delete_package(client):
    """Test delete of package"""


def test_package_upload(client, tmpdir, admin_headers, monkeypatch):
    """Test upload of a package"""
    f = tmpdir.join("test")
    f.write("a simple test")
    valid_data = {
        ':action': 'file_upload',
        'name': 'uploaded',
        'summary': 'from unittests',
        'description': 'simple upload test',
        'download_url': '',
        'home_page': '',
        'version': '0.1',
        'keywords': ['test', 'other'],
        'md5_digest': 'badhash',
        'file': (f.open('rb'), 'test-0.1.tar.gz')
    }
    resp = client.post('/simple/', headers=admin_headers, data=valid_data)
    assert resp.status_code == 200

    # bad action
    resp = client.post('/simple/', headers=admin_headers,
                       data={':action': 'bad'})
    assert resp.status_code == 400

    # bad data
    data = {
        ':action': 'file_upload'
    }
    resp = client.post('/simple/', headers=admin_headers, data=data)
    assert resp.status_code == 400

    # monkey patch db to raise exception
    def raise_db(obj):
        raise Exception()
    monkeypatch.setattr(db.session, 'commit', raise_db)
    valid_data['file'] = (f.open('rb'), 'test-0.1.tar.gz')
    resp = client.post('/simple/', headers=admin_headers, data=valid_data)


def test_list_users(client, users, admin_headers):
    """Test list users view"""
    resp = client.get('/dashboard/users/')
    assert resp.status_code == 200
    data = resp.get_data(as_text=True)

    for u in users:
        assert u.username in data
        assert u.email in data


def test_create_users(client, admin_headers):
    """Test creation of a new user"""
    # just getting the page
    resp = client.get('/dashboard/users/create', headers=admin_headers)
    assert resp.status_code == 200

    data = {
        'username': 'newuser',
        'email': 'newuser@mail.com',
        'password': 'test',
        'confirm': 'test',
        'active': 'y'
    }
    resp = client.post('/dashboard/users/create',
                       headers=admin_headers, data=data)
    assert resp.status_code == 302

    resp = client.get('/dashboard/users/')
    assert 'newuser' in resp.get_data(as_text=True)
    assert 'email' in resp.get_data(as_text=True)


def test_view_user(client, user, admin_headers):
    """Test simple get of a user"""
    resp = client.get('/dashboard/users/%d' % user.id, headers=admin_headers)
    assert resp.status_code == 200

    assert user.username in resp.get_data(as_text=True)
    assert user.email in resp.get_data(as_text=True)


def test_update_user(client, user, admin_headers):
    """Test update of a user"""
    data = {
        'username': 'updated',
        'email': user.email,
        'active': 'y'
    }
    resp = client.post('/dashboard/users/%d' % user.id, headers=admin_headers,
                       data=data)
    assert resp.status_code == 302

    user = User.query.filter_by(id=user.id).first()
    assert user.username == 'updated'
    assert user.email == data['email']


def test_delete_user(client, user, admin_headers):
    """Test deletion of a user"""
    user_id = user.id
    resp = client.get('/dashboard/users/delete/%d' % user_id, headers=admin_headers)
    assert resp.status_code == 302

    assert User.query.filter_by(id=user_id).first() is None
