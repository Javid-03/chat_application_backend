from fastapi import Depends, HTTPException,status
from jose import JWTError,jwt
from fastapi.security.oauth2 import OAuth2PasswordBearer




SECRET_KEY="acthjgknjuhyrthgjhkljhgtyyf"
ALGORITHM='HS256'

# outh2_customer_scheme=OAuth2PasswordBearer(tokenUrl="token")

def verify_customer_access_token(token: str):

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("customer_id")
        # print(id)
        
        if id is None:
            raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        
        # user=db.register.find_one({"_id":ObjectId(id)})
        # user["_id"]=str(user["_id"])
        # print(type(payload))
    except JWTError:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    return payload



def verify_access_token(token: str):

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        
        if id is None:
            raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        
        # user=db.register.find_one({"_id":ObjectId(id)})
        # user["_id"]=str(user["_id"])
        print(type(payload))
    except JWTError:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    return payload