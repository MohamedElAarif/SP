import time
from typing import Dict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import redis
from app.config import settings

# Redis client for rate limiting
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed based on rate limit"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_size
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, self.window_size)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests < self.requests_per_minute
        except Exception as e:
            # If Redis is not available, allow the request
            print(f"Rate limiter error: {e}")
            return True

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the current window"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_size
            
            # Remove old entries and count current requests
            redis_client.zremrangebyscore(key, 0, window_start)
            current_requests = redis_client.zcard(key)
            
            return max(0, self.requests_per_minute - current_requests)
        except Exception:
            return self.requests_per_minute

# Global rate limiter instance
rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded IP first (for reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    return request.client.host

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    client_ip = get_client_ip(request)
    rate_key = f"rate_limit:{client_ip}"
    
    if not rate_limiter.is_allowed(rate_key):
        remaining = rate_limiter.get_remaining_requests(rate_key)
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Too many requests.",
                "retry_after": 60,
                "remaining_requests": remaining
            },
            headers={
                "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time()) + 60)
            }
        )
    
    response = await call_next(request)
    
    # Add rate limit headers to response
    remaining = rate_limiter.get_remaining_requests(rate_key)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response
