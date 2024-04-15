from database.database import AsyncSessionLocal, User
import random

def select_random_user(exclude_user_id=None):
    db = AsyncSessionLocal()
    if exclude_user_id:
        users = db.query(User).filter(User.telegram_id != exclude_user_id).all()
    else:
        users = db.query(User).all()

    db.close()
    if users:
        return random.choice(users)
    return None
