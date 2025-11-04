from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel
from datetime import datetime, timedelta


app = FastAPI()

# Parameters

# Time interval since first request, after which the counter is reset
waiting_time_in_seconds = 20 
# Maximum number of requests per time period
max_count_of_requests = 3 
# Routes that do not use the rate limiter
routes_without_lock = ["/docs", "/openapi.json"] 

# The dictionary contains the IP as a key and the RequestCount object as a value
requests_dict: dict[str, RequestsCount] = {} 

class RequestsCount(BaseModel):
    ip: str 
    time_of_first_request: datetime = datetime.now()
    count_of_request: int = 1


@app.middleware("http")
async def query_limiter_middleware(request: Request, call_next: callable):
    response = await call_next(request)

    if request.url.path in routes_without_lock:
        return response

    ip_address = request.client.host

    if ip_address in requests_dict:
        request_object = requests_dict[ip_address]

        # Reset counter if enough time has passed since the first request
        if datetime.now() - request_object.time_of_first_request >= timedelta(seconds=waiting_time_in_seconds):
            request_object.count_of_request = 0
            request_object.time_of_first_request = datetime.now()
        # Return error if the user has exceeded the request limit
        if request_object.count_of_request >= max_count_of_requests:
            return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content="Too many request")
        
        #Counting requests
        request_object.count_of_request += 1
    else:
        # If this first request from ip
        requests_dict[ip_address] = RequestsCount(ip=ip_address, count=1)

    # Log
    print(f"IP: {ip_address} request object {requests_dict[ip_address]}")

    return response


@app.get("/")
async def main():
    return {"message": "done"}