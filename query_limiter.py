from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from datetime import datetime, timedelta


app = FastAPI()

class RequestsCount(BaseModel):
    ip: str
    time_of_first_request: datetime = datetime.now()
    count_of_request: int = 0

requests_dict: dict[str, RequestsCount] = {}
waiting_time_in_seconds = 20
max_count_of_requests = 3

@app.middleware("http")
async def query_limiter_middleware(request: Request, call_next: callable):
    ip_address = request.client.host
    if ip_address in requests_dict:
        request_object = requests_dict[ip_address]
        if datetime.now() - request_object.time_of_first_request >= timedelta(seconds=waiting_time_in_seconds):
            request_object.count_of_request = 0
            request_object.time_of_first_request = datetime.now()
        if request_object.count_of_request >= max_count_of_requests:
            return Response(status_code=429, content="Too many request")
        request_object.count_of_request += 1
    else:
        requests_dict[ip_address] = RequestsCount(ip=ip_address, count=1)

    print(f"IP: {ip_address} request object {requests_dict[ip_address]}")

    return await call_next(request)


@app.get("/")
async def main():
    return {"message": "done"}