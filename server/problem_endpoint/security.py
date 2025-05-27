from fastapi import Depends, HTTPException
import os
from fastapi.security.api_key import APIKeyHeader


api_key_header = APIKeyHeader(name="api-key")


def verify_api_key(api_key: str = Depends(api_key_header)) -> None:
    """
    Verify the provided API key. Raise an error if invalid.
    """
    expected_api_key = os.getenv("IRB_API_KEY")
    if expected_api_key is None:
        raise HTTPException(status_code=500, detail="API Key not set")
    if api_key != expected_api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
