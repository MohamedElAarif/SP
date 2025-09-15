import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base, User
from app.auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    # Create a test user
    db = TestingSessionLocal()
    test_user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword")
    )
    db.add(test_user)
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers(setup_database):
    # Login to get token
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_scrape_job(auth_headers):
    response = client.post(
        "/api/scrape/",
        json={
            "url": "https://example.com",
            "selectors": {
                "title": "h1",
                "links": "a"
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["status"] == "pending"

def test_create_scrape_job_unauthorized():
    response = client.post(
        "/api/scrape/",
        json={
            "url": "https://example.com",
            "selectors": {
                "title": "h1"
            }
        }
    )
    assert response.status_code == 401

def test_get_scrape_result(auth_headers):
    # First create a job
    create_response = client.post(
        "/api/scrape/",
        json={
            "url": "https://example.com",
            "selectors": {
                "title": "h1"
            }
        },
        headers=auth_headers
    )
    job_id = create_response.json()["id"]
    
    # Then get the result
    response = client.get(
        f"/api/scrape/{job_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["url"] == "https://example.com"

def test_delete_scrape_job(auth_headers):
    # First create a job
    create_response = client.post(
        "/api/scrape/",
        json={
            "url": "https://example.com",
            "selectors": {
                "title": "h1"
            }
        },
        headers=auth_headers
    )
    job_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(
        f"/api/scrape/{job_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(
        f"/api/scrape/{job_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404
