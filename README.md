# Kakulus Backend

Simple FastAPI backend for collecting KYC data and admin management using Astra DB (via `astrapy`).

## Summary
- API to submit KYC data (with large base64 chunking), create/delete admins, login, and access an admin dashboard.
- Stores data in Astra DB collections: `user_kyc_data` and `admin_data`.

## Requirements
- Python 3.9+
- Install dependencies from `requirements.txt` (recommended):

```bash
pip install -r requirements.txt
```

Typical dependencies (already used in the code):
- fastapi
- uvicorn
- astrapy
- python-dotenv
- argon2-cffi
- python-jose
- apscheduler

## Environment Variables
Create a `.env` file with the following keys used by the code. Example values are for illustration only — replace with your real values.

`.env.example` (copy to `.env` and fill in):

```env
# Astra DB
DATABASE_URL=https://your-database-id.apps.astra.datastax.com
DATABASE_TOKEN=your_astra_token

# Frontend
FRONTEND_URL=http://localhost:3000

# JWT
ALGORITHM=JWT algorithm (e.g. HS256)
SECRET_KEY=supersecretkey

# Email (used by send_email_otp)
SENDER_EMAIL=youremail@gmail.com
PASSWORD=your_email_password_or_app_password
```

## Running
1. Install dependencies.
2. Create `.env` with the variables above.
3. Start the app:

```bash
uvicorn app:app --reload
```

## API Endpoints

- `POST /submit_kyc` — submit KYC JSON payload. Fields that may contain large base64 strings (`profile_picture`, `signature`, `utility_bill`, `means_of_id`) are automatically chunked into 4000-character pieces before storing.

- `POST /create_admin` — create an admin. Request model: `Admin` (from `model.py`): `email`, `password` (plain text, hashed server-side).

- `DELETE /delete_admin/{admin_email}` — delete admin by email.

- `GET /delete_kyc/{id}` — delete KYC record by `_id`.

- `POST /login` — admin login. Request model: `LoginData` (`email`, `password`). Returns `token` and `userId` on success. The refresh token is stored in the admin record.

- `POST /admin_dashboard` — protected route. Requires `Authorization: Bearer <token>` header. Uses HTTP Bearer auth and token verification logic in `utill.py`.

## Models
Located in `model.py`:

- `Admin` — `email: EmailStr`, `password: str`, `refresh_token: str | None`
- `LoginData` — `email: EmailStr`, `password: str`
- `OtpVerify` — `id: str`, `otp: str`

## Utilities
Located in `utill.py`:

- Token helpers: `create_access_token`, `verify_access_token`, `verify_refresh_token`.
- Password hashing: `hashedpassword`, `VerifyHashed` (argon2 PasswordHasher).
- OTP helpers: `generate_otp`, `send_email_otp` (uses Gmail SMTP configuration from env).

## Notes & Tips
- The app uses `astrapy.DataAPIClient` to interact with Astra DB. Ensure your `DATABASE_TOKEN` and `DATABASE_URL` are correct and have the required permissions to create/modify collections.
- When sending very large base64 assets in `POST /submit_kyc`, they will be split into smaller chunks to stay below size limits.
- The token refresh flow in `get_current_admin` attempts to detect expired access tokens and issue a short-lived new access token if the stored refresh token is valid.

## Example Requests

Login (curl):

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"yourpassword"}'
```

Submit KYC (example):

```bash
curl -X POST http://127.0.0.1:8000/submit_kyc \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","profile_picture":"<base64-string>", "id_number":"123"}'
```

## Next steps
- Add or verify `requirements.txt` in the project root.
- Add unit tests and integration checks for the auth flow.

If you want, I can add a `requirements.txt` and create a `.env.example` file now.
