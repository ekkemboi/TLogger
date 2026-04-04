# TradeLogger - Agent Guidelines

TradeLogger is a trade journaling system with a Flask backend, PostgreSQL database, and Electron desktop widget for manual trade entry. The web dashboard displays metrics and trade history using a **v2 sidebar design with HTMX for SPA-like navigation**.

### Recent Updates (v2 Sidebar Redesign)
- **Layout**: Left sidebar (260px) instead of top navbar
- **Colors**: Green primary (#22C55E) instead of amber
- **Font**: System font stack (Inter removed)
- **Navigation**: HTMX-powered SPA-like navigation (sidebar persists)
- **Authentication**: Login page with theme toggle and "remember me" checkbox

## Build & Development

```bash
# Setup
cd ~/PROJECTS/TradeLogger
source .venv/bin/activate          # or: uv sync

# Start database (Docker)
sg docker -c "docker compose up -d postgres"

# Run Flask server
python -m src.app                  # http://localhost:5000

# Run all tests
python -m pytest tests/ -v

# Run single test
python -m pytest tests/test_trades.py::TestCreateTrade::test_create_trade_success -v

# Run tests by class
python -m pytest tests/test_trades.py::TestGetTrades -v

# Run tests by keyword
python -m pytest tests/ -k "create_trade" -v

# Desktop widget (Electron)
cd desktop && bun start
```

## Project Structure

```
src/
  app.py              # Flask app factory
  config.py           # Dev/Test/Prod configs
  models.py           # SQLAlchemy models (Trade, FavoriteProduct)
  routes/             # API blueprints (trades, metrics, favorites)
  services/           # Business logic (TradeService)
web/
  templates/          # Jinja2 templates (dashboard, trades, favorites)
  routes/             # Web page routes
desktop/
  renderer/           # Electron widget (index.html, widget.js, widget.css)
tests/
  conftest.py         # Fixtures (app, client, sample_trade_data)
  test_trades.py      # Trade API tests
  test_metrics.py     # Metrics API tests
```

## HTMX Navigation

The v2 redesign uses HTMX for SPA-like navigation:
- Sidebar persists across page transitions (no full reloads)
- `hx-get` attributes on sidebar links trigger AJAX requests
- `hx-target="main"` swaps only the content area
- `hx-push-url="true"` updates browser URL
- `withCredentials: true` ensures authentication cookies are sent

### Template Structure
```html
<!-- base.html - Single content block definition -->
{% if not htmx_request %}
  <!-- Sidebar, scripts, global handlers -->
{% endif %}
<main>
  {% block content %}{% endblock %}
</main>
{% if not htmx_request %}
  <!-- Footer scripts -->
{% endif %}
```

## Code Style

### Imports
- Standard library first, then third-party, then local
- Use absolute imports: `from src.models import Trade`
- Alphabetize within groups

### Naming
- **snake_case** for functions, variables, methods
- **PascalCase** for classes (e.g., `TradeService`, `TradeDirection`)
- **UPPER_SNAKE_CASE** for enum values and constants
- Blueprints named with `_bp` suffix: `trades_bp`

### Types & Documentation
- All public functions require docstrings (one-line `"""Summary."""`)
- Use `Decimal` for monetary values (never float in calculations)
- Convert Decimal to float only in `to_dict()` for JSON serialization

### Error Handling
- Return `(jsonify({"error": "message"}), 400)` for client errors
- Return `jsonify({"error": "Not found"}), 404` for missing resources
- Validate required fields at route level before calling services

### Models
- UUID primary keys: `db.Column(db.String(36), default=lambda: str(uuid.uuid4()))`
- Enum columns: `db.Column(db.Enum(TradeDirection))`
- JSON columns for arrays/objects: `db.Column(db.JSON)`
- Always implement `to_dict()` and `__repr__()`

### Routes
- Use Blueprint pattern: `bp = Blueprint("name", __name__)`
- Services contain business logic, routes handle HTTP
- Accept both JSON (`request.get_json()`) and multipart (`request.form`)
- Swagger docstrings on route functions (YAML after `---`)

### Testing
- Use pytest fixtures defined in `conftest.py`
- Each test function gets a fresh database (function-scoped `app` fixture)
- Test class per endpoint: `TestCreateTrade`, `TestGetTrades`
- Use `client.post()` with `data=json.dumps(payload)`, `content_type="application/json"`

## API Patterns

### Create resource
```python
@bp.route("/resources", methods=["POST"])
def create_resource():
    data = request.get_json()
    if not data or "required_field" not in data:
        return jsonify({"error": "Missing required_field"}), 400
    resource = Service.create(data)
    return jsonify(resource.to_dict()), 201
```

### List with filters
```python
filters = {k: v for k, v in request.args.items() if v is not None}
pagination = Service.get_all(filters, page, per_page)
return jsonify({"items": [i.to_dict() for i in pagination.items], "total": pagination.total})
```

## Key Business Rules

- P&L = `(price_diff × position_size × point_value) - fees`
- Point value and default fees come from `FavoriteProduct`
- `take_profit` field serves as the exit price for closed trades
- `exit_transactions` array tracks partial exits with qty, exit_price, fees
- Trade status: `CONFIRMED` (open) → `CLOSED` (has take_profit or exit_transactions)
