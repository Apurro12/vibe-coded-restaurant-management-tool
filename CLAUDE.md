# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based restaurant inventory management system called "14_mama". It's a simple web application that allows restaurant staff to manage inventory items, track stock movements, and view available items.

## Commands

### Running the Application
```bash
cd app
python app.py
```
The application runs on `http://localhost:5000` with debug mode enabled.

### Dependencies
```bash
cd app
pip install -r requirements.txt
```
Only Flask is required as a dependency.

### Database
The application uses SQLite with the database file `inventory.db` stored in the app directory. The database is automatically created when the application starts if it doesn't exist.

## Code Architecture

### Application Structure
- `app/app.py` - Main Flask application with all routes and database logic
- `app/templates/` - Jinja2 HTML templates for the web interface
- `app/inventory.db` - SQLite database file (created automatically)

### Database Schema
Single table `inventory`:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT NOT NULL) - Item name
- `quantity` (INTEGER NOT NULL) - Current stock quantity
- `unit` (TEXT NOT NULL) - Unit of measurement (e.g., "kg", "pieces")

### Routes and Functionality
- `/` - Main page displaying all inventory items
- `/available` - View all available items with edit/delete actions
- `/add` - Add new inventory items
- `/movement/<id>` - Adjust stock quantities (add/remove stock)
- `/delete/<id>` - Delete inventory items

### Key Patterns
- All database connections use `get_db_connection()` helper function
- Database connections are properly closed after each operation
- Templates use Milligram CSS framework for styling
- Form submissions use POST method with proper redirects
- Stock movements allow positive (add) or negative (remove) quantity changes

### Frontend
- Uses Milligram CSS framework via CDN
- Simple responsive design with max-width of 600px
- Consistent styling across all pages
- JavaScript confirmation for delete operations

## Development Notes

- The application is designed for local development with debug mode enabled
- No authentication or user management implemented
- Direct SQL queries without ORM (uses sqlite3 module)
- Template references to `/edit/<id>` route exist but the route is not implemented in app.py
- Database operations use parameterized queries to prevent SQL injection