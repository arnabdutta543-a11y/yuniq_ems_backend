import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    # If the password in DB is plain text (e.g. from seed data), fallback to direct comparison.
    # Standard bcrypt hashes usually start with $2a$, $2b$, or $2y$
    is_hashed = hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$") or hashed_password.startswith("$2y$")
    if not is_hashed:
        return plain_password == hashed_password
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback if parsing/verification fails
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
