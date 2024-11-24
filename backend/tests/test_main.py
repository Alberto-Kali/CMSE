import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app, parse_and_save_pdf, UserManager, CompetitionSearcher, TravelService

client = TestClient(app)

@pytest.fixture
def mock_pdf_parser():
    with patch('modules.pdf_parser.PDFParser') as mock:
        yield mock

@pytest.fixture
def mock_db_connection():
    with patch('psycopg2.connect') as mock:
        yield mock

def test_upload_pdf_db_invalid_extension():
    response = client.post(
        "/upload_pdf_db",
        files={"file": ("test.txt", b"some content")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed."

def test_get_events_no_keywords():
    response = client.get("/get_events")
    assert response.status_code == 400
    assert response.json()["detail"] == "No keywords provided for search."

@patch('modules.rag_controller.CompetitionSearcher')
def test_get_events_success(mock_searcher):
    mock_searcher.return_value.search_competitions_by_keywords.return_value = [
        ("Sport1", "Individual", "EKP123", "2024-01-01", "2024-01-02", "City1", 
         "Discipline1", "Class1", "Country1", 10, "M18-25")
    ]
    
    response = client.get("/get_events?keywords=sport")
    assert response.status_code == 200
    assert len(response.json()["events"]) == 1

@patch('modules.router_conroller.TravelService')
def test_travel_info_success(mock_travel):
    mock_travel.return_value.get_hotel_price.return_value = "100"
    mock_travel.return_value.get_transport_price.return_value = "50"
    
    response = client.get("/travel_info?departure_city=City1&arrival_city=City2&check_in=2024-01-01&check_out=2024-01-02")
    assert response.status_code == 200
    assert response.json() == {"hotel_price": "100", "transport_price": "50"}

def test_register_user_success():
    test_user = {
        "username": "testuser",
        "email": "test@test.com",
        "phone": "1234567890",
        "name": "Test User",
        "description": "Test description",
        "avatar": "avatar.jpg",
        "birth": "1990-01-01",
        "city": "Test City",
        "sports": ["Sport1"],
        "password": "testpass"
    }
    
    with patch('modules.users_controller.UserManager') as mock_user_manager:
        response = client.post("/register_user", params=test_user)
        assert response.status_code == 200
        assert response.json()["message"] == "User  registered successfully."

def test_auth_user_invalid_credentials():
    with patch('modules.users_controller.UserManager') as mock_user_manager:
        mock_user_manager.return_value.login_user.return_value = False
        response = client.post("/auth_user?username=testuser&password=wrongpass")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password."

def test_get_sport_names_success():
    with patch('psycopg2.connect') as mock_conn:
        mock_cursor = Mock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("Sport1",), ("Sport2",)]
        
        response = client.get("/get_sport_names")
        assert response.status_code == 200
        assert response.json() == {"sport_names": ["Sport1", "Sport2"]}

def test_comment_event_invalid_rate():
    response = client.post(
        "/comment_event/1/1?rate=6&text=test"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Rate must be between 0 and 5."

def test_register_for_event_full():
    with patch('psycopg2.connect') as mock_conn:
        mock_cursor = Mock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (2, [1, 2])  # max_people_count=2, peoples=[1,2]
        
        response = client.post("/register_for_event/1/3")
        assert response.status_code == 400
        assert response.json()["detail"] == "Event is full."
