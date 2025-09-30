# Secure Login System

## Overview
The Secure Login System (SLS) is a web application designed to provide safe and reliable user authentication. It uses Flask for the backend and MySQL for storing user data, while Bcrypt ensures passwords are securely encrypted. JWT tokens are used for managing sessions, and Google reCAPTCHA protects the system from bots and automated attacks. The project focuses on creating a simple yet secure login process that can be applied to websites, portals, or any platform that requires user verification.

---

## Features
- Passwords are encrypted using Bcrypt for strong protection.
- JWT tokens are used to manage user sessions safely.
- User credentials are stored and managed in a MySQL database.
- Google reCAPTCHA is integrated to block bots and automated attacks.
- A role based access is implemented:
  - Admin can promote/demote user, delete accounts, track user login/logout time.
  - Users can view their dashboard. 
---

## Screenshots

### Login Page
![Login Page]()
