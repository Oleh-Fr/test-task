## Project Structure
```
├── app/
│   ├── main.py                 
│   ├── websocket_manager.py   
│   ├── db/
│   │   ├── base.py            
│   │   ├── db.py               # Engine, session, lifespan, background tasks
│   │   └── models.py           
│   └── schemas/
│       └── schemas.py          
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```
## Getting Started
### Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/oleh-fr/test-task.git
   cd test-task
   ```
2. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` as needed (defaults work out of the box):
   ```env
   POSTGRES_USER=user
   POSTGRES_PASSWORD=some_password
   POSTGRES_DB=lots
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```
3. **Start the application:**
   ```bash
   docker-compose up --build
   ```
4. The API is available at **http://localhost:8000**
5. Interactive API docs (Swagger UI) at **http://localhost:8000/docs**
## API Reference
### Lots
#### `GET /lots`
Returns all currently running auction lots.
**Response:**
```json
[
  {
    "id": 1,
    "title": "Vintage Watch",
    "current_price": 150.0,
    "status": "running",
    "end_time": "25 June 2025, 14:30:00"
  }
]
```
#### `POST /lots`
Create a new auction lot.
**Request body:**
```json
{
  "title": "Vintage Watch",
  "start_price": 100.0,
  "duration_seconds": 300
}
```
### Bids
#### `POST /lots/{lot_id}/bids`
Place a bid on a lot. The bid amount must exceed the current price.
**Request body:**
```json
{
  "bidder": "alice",
  "amount": 150.0
}
```
**Response:**
```json
{
  "message": "Bid placed",
  "current_price": 150.0,
  "end_time": "2025-06-25T14:30:00"
}
```
**Error responses:**
| Status | Reason                              |
|--------|-------------------------------------|
| 404    | Lot not found                       |
| 400    | Auction ended                       |
| 400    | Bid too low (must exceed current price) |
### WebSocket
#### `wscat -c ws://localhost:8000/ws/lots/{lot_id}`
Connect to receive real-time updates for a specific lot. When a bid is placed, all connected clients receive:
```json
{
  "type": "bid_placed",
  "lot_id": 1,
  "bidder": "alice",
  "amount": 150.0,
  "new_end_time": "2025-06-25T14:30:00"
}
```
