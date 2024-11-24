"""
Provides a FastAPI application for managing competitions, user registration and authentication, and travel information.

The application includes the following main features:
- Uploading PDF files and parsing the data to store in a PostgreSQL database
- Searching for competitions based on keywords
- Retrieving travel information (hotel prices and transport prices) between two cities
- Registering and authenticating users
- Editing and deleting user profiles
- Registering users for events
- Retrieving a list of unique sport names from the competitions
- Submitting comments for events

The application uses the FastAPI framework, PostgreSQL database, and various utility modules to implement the functionality.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from typing import Dict, List, Optional
import os
import psycopg2
from concurrent.futures import ThreadPoolExecutor
from modules.pdf_parser import PDFParser
from modules.users_controller import UserManager
from modules.rag_controller import CompetitionSearcher
from modules.router_conroller import TravelService

POSTGRES_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(POSTGRES_URL)
cursor = conn.cursor()

app = FastAPI()

# Create a ThreadPoolExecutor for background tasks
executor = ThreadPoolExecutor(max_workers=2)

def parse_and_save_pdf(file_path: str):
    try:
        # Parse the PDF and extract data
        pdf_parser = PDFParser()
        parsed_data = pdf_parser.parse(file_path)
        
        # Insert parsed data into the PostgreSQL database
        for entry in parsed_data:
            sport_name, sport_composition, ekp_number, date_start, date_end, city, discipline, competition_class, country, max_people_count, genders_and_ages = entry
            
            # Check if the event already exists
            cursor.execute("SELECT COUNT(*) FROM competitions WHERE ekp_number = %s", (ekp_number,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.execute("""
                    INSERT INTO competitions (sport_name, sport_composition, ekp_number, date_start, date_end, city, discipline, competition_class, country, max_people_count, peoples, genders_and_ages, comments)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (sport_name, sport_composition, ekp_number, date_start, date_end, city, discipline, competition_class, country, max_people_count, [], genders_and_ages, []))
        
        # Commit the transaction
        conn.commit()
        
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        # Handle the error (e.g., log it, notify an admin, etc.)


@app.post("/upload_pdf_db")
async def upload_pdf_db(file: UploadFile = File(...)):
    # Ensure the uploaded file is a PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # Save the uploaded file temporarily
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())
    
    # Start a new thread to parse the PDF and save data
    executor.submit(parse_and_save_pdf, temp_file_path)

    # Return a success message immediately
    return {"message": "PDF upload received. Processing in the background."}


@app.get("/get_events")
async def get_events(keywords: Optional[str] = Query(None)):
    """Retrieve events based on keywords."""
    if not keywords:
        raise HTTPException(status_code=400, detail="No keywords provided for search.")

    try:
        searcher = CompetitionSearcher(POSTGRES_URL)
        searcher.fetch_competitions()  # Fetch competitions data from the database
        searcher.create_feature_vectors()  # Create feature vectors
        results = searcher.search_competitions_by_keywords(keywords)  # Search by keywords
        searcher.close()  # Close the database connection

        if not results:
            return {"message": "No events found matching the keywords."}

        # Format results for output
        formatted_results = []
        for result in results:
            formatted_results.append({
                "sport_name": result[0],
                "sport_composition": result[1],
                "ekp_number": result[2],
                "date_start": result[3],
                "date_end": result[4],
                "city": result[5],
                "discipline": result[6],
                "competition_class": result[7],
                "country": result[8],
                "max_people_count": result[9],
                "genders_and_ages": result[10]
            })

        return {"events": formatted_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving events: {str(e)}")


@app.get("/travel_info")
async def travel_info(
    departure_city: str,
    arrival_city: str,
    check_in: str,
    check_out: str,
    adults: Optional[int] = 2
) -> Dict[str, str]:
    """
    Получает информацию о ценах на отели и транспорт между городами.
    
    :param departure_city: Город отправления.
    :param arrival_city: Город назначения.
    :param check_in: Дата заселения (в формате YYYY-MM-DD).
    :param check_out: Дата выселения (в формате YYYY-MM-DD).
    :param adults: Количество гостей (по умолчанию 2).
    :return: Словарь с информацией о ценах на отели и транспорт.
    """
    try:
        travel_service = TravelService()  # You can pass a token if needed
        
        # Get hotel prices in the arrival city
        hotel_price = travel_service.get_hotel_price(arrival_city, check_in, check_out, adults=adults)
        
        # Assuming you have a method to calculate transport prices
        transport_price = travel_service.get_transport_price(departure_city, arrival_city, check_out, api_key="YOUR_API_KEY")

        return {
            "hotel_price": hotel_price,
            "transport_price": transport_price
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching travel information: {str(e)}")

@app.get("/ai_route")
async def get_events():
    return {"message": "NO MODEL!"}


@app.post("/register_user")
async def register_user(
    username: str,
    email: str,
    phone: str,
    name: str,
    description: str,
    avatar: str,
    birth: str,
    city: str,
    sports: List[str],
    password: str
):
    """Register a new user."""
    try:
        user_manager = UserManager(POSTGRES_URL)
        user_manager.register_user(
            username=username,
            email=email,
            phone=phone,
            name=name,
            description=description,
            avatar=avatar,
            birth=birth,
            city=city,
            sports=sports,
            events=[],  # New users start with no events
            password=password
        )
        return {"message": "User  registered successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

@app.post("/auth_user")
async def auth_user(username: str, password: str):
    """Authenticate a user."""
    try:
        user_manager = UserManager(POSTGRES_URL)
        if user_manager.login_user(username, password):
            return {"message": "Login successful."}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging in: {str(e)}")

@app.put("/edit_user/{user_id}")
async def edit_user(user_id: int, user_data: Dict):
    """Edit user details."""
    try:
        user_manager = UserManager(POSTGRES_URL)
        user_manager.edit_user(user_id, **user_data)
        return {"message": "User  updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    """Delete a user."""
    try:
        user_manager = UserManager(POSTGRES_URL)
        user_manager.delete_user(user_id)
        return {"message": "User  deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@app.post("/register_for_event/{event_id}/{user_id}")
async def register_for_event(event_id: int, user_id: int):
    """Register a user for an event if not full."""
    try:
        user_manager = UserManager(POSTGRES_URL)
        
        # Check if the event exists
        cursor.execute("SELECT max_people_count, peoples FROM competitions WHERE id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found.")
        
        max_people_count, peoples = event
        
        # Check if the event is full
        if len(peoples) >= max_people_count:
            raise HTTPException(status_code=400, detail="Event is full.")
        
        # Register user for the event
        peoples.append(user_id)  # Add user ID to the event's peoples list
        cursor.execute("UPDATE competitions SET peoples = %s WHERE id = %s", (peoples, event_id))
        
        # Add event ID to the user's events list
        cursor.execute("UPDATE users SET events = array_append(events, %s) WHERE id = %s", (event_id, user_id))
        
        conn.commit()  # Commit the changes
        return {"message": "User  registered for the event successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering for event: {str(e)}")

@app.get("/get_sport_names")
async def get_sport_names() -> Dict[str, List[str]]:
    """Retrieve all unique sport names from the competitions."""
    try:
        cursor.execute("SELECT DISTINCT sport_name FROM competitions")
        sport_names = cursor.fetchall()
        
        # Extract sport names from the fetched results
        unique_sport_names = [sport[0] for sport in sport_names]

        return {"sport_names": unique_sport_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sport names: {str(e)}")

@app.post("/comment_event/{event_id}/{user_id}")
async def comment_event(
    event_id: int,
    user_id: int,
    rate: int,
    text: str,
    images: List[str] = []
):
    """Submit a comment for an event."""
    try:
        # Validate the rate
        if rate < 0 or rate > 5:
            raise HTTPException(status_code=400, detail="Rate must be between 0 and 5.")

        # Create the comment structure
        comment = {
            "user_id": user_id,
            "rate": rate,
            "text": text,
            "images": images
        }

        # Insert the comment into the event's comments array
        cursor.execute("""
            UPDATE competitions 
            SET comments = array_append(comments, %s) 
            WHERE id = %s
        """, (comment, event_id))
        
        conn.commit()  # Commit the changes
        return {"message": "Comment submitted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting comment: {str(e)}")

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to CMSE Backend!"}