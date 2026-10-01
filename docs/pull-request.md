## Summary

Implement a Theatre API portfolio project with Django REST Framework.

- CRUD for genres, actors, theatre halls, plays and performances.
- Nested catalog list responses, optimized queries, filters and pagination.
- JWT authentication, registration and current-user profile.
- Reservations with multiple tickets and access restricted to the owner.
- Seat validation, duplicate booking prevention and atomic reservation creation.
- Swagger/OpenAPI documentation and local setup/access instructions.

## Additional functionality

`GET /api/performances/` includes `tickets_available`, calculated separately for
each performance as hall capacity minus reserved tickets. Invalid date filters,
including impossible calendar dates, return 400.

## Verification

- `python manage.py test`: 29 tests passed.
- `python manage.py check`: no issues.
- `python manage.py spectacular --file schema.yml --validate`: passed.
- `flake8 --exclude .venv,.git,.idea --statistics --count .`: 0 errors.
- Local setup, authentication and booking flow verified from a clean database.

## Database structure

![Database diagram](https://raw.githubusercontent.com/2d1Corp/theater-api/develop/docs/theatre-schema.png)

[Editable draw.io source](https://github.com/2d1Corp/theater-api/blob/develop/docs/theatre-schema.drawio)

## Browsable API screenshots

### Performances

![Performances](https://raw.githubusercontent.com/2d1Corp/theater-api/develop/docs/screenshots/performance-list.jpg)

### Plays

![Plays](https://raw.githubusercontent.com/2d1Corp/theater-api/develop/docs/screenshots/play-list.jpg)

### Theatre halls

![Halls](https://raw.githubusercontent.com/2d1Corp/theater-api/develop/docs/screenshots/hall-list.jpg)
