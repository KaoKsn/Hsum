import bcrypt


class PasswordTooLongError(Exception):
    """Raised when a password exceeds bcrypt's 72-byte limit."""


class passwordHasher:
    MAX_BYTES = 72

    @classmethod
    def validate(cls, password: str) -> bool:
        if len(password.encode("utf-8")) > cls.MAX_BYTES:
            raise PasswordTooLongError(
                f"Please enter as password thats fits the under {cls.MAX_BYTES} bytes frame."
            )
        return True

    @classmethod
    def hash(cls, password: str) -> str:
        cls.validate(password)
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

    @classmethod
    def check_password(cls, password: str, password_hash: str) -> bool:
        """
        Compare the stored password hash and the password sent

        The caller isn't expected to pass the hashed password as bytes.
        """
        cls.validate(password)
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
