# app Folder
This folder contains the core application logic.
 # app Folder

 This folder contains the core application logic for the restaurant system.

 ## Files (detailed)

 - `__init__.py` — App factory and extensions
	 - Creates the Flask app via `create_app()`.
	 - Initializes `SQLAlchemy`, `Flask-Migrate`, `Flask-Login`, and registers blueprints (`auth`, `routes`, `admin`, `views`).
	 - Calls `init_sockets` to initialize Socket.IO for the app.

 - `models.py` — Database models and serializers
	 - Maps Python models to the existing database tables: `Employee` (used by `User`), `Customer`, `Product`, `Orders` (`Order`), and `Order_Line` (`OrderLine`).
	 - Adds relationships (e.g., Order.lines) and `to_dict()` methods that return snake_case JSON keys for API responses.

 - `auth.py` — Authentication routes
	 - Handles login and logout using `Flask-Login`.
	 - Login route checks the user credentials and redirects users to the appropriate role dashboard (`front`, `kitchen`, `admin`).

 - `config.py` — Configuration
	 - Loads environment variables (via python-dotenv) and exposes a `Config` class.
	 - Key settings: `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_TRACK_MODIFICATIONS`, `SECRET_KEY`.

 - `routes.py` — Main application routes and JSON API
	 - Contains HTML form endpoints used by staff dashboards (`/front`, `/kitchen`).
	 - Implements JSON REST endpoints for Orders and OrderLines:
		 - `GET /api/orders`, `GET /api/orders/<id>`
		 - `POST /api/orders` (creates order header + lines)
		 - `PUT/PATCH /api/orders/<id>` (admin header updates)
		 - `DELETE /api/orders/<id>` (admin only)
		 - `POST /api/order_lines`, `PATCH /api/order_lines/<id>/status`
	 - Emits Socket.IO events (`order_new`, `order_update`, `order_delete`) when resources change.
	 - Implements role-based checks: `front`, `kitchen`, `admin`.

 - `admin.py` — Admin dashboard and user management
	 - Renders the admin dashboard (`/admin/dashboard`).
	 - Exposes admin-only JSON endpoints to manage users (create, list, update, delete).

 - `sockets.py` — Socket.IO initialization
	 - Creates the global `socketio` object and provides `init_sockets(app)` to initialize it with the Flask app and configure CORS/async mode.
	 - Registers simple connect/disconnect handlers and is the central place to manage realtime behavior.

 - `utils.py` — Helper utilities
	 - Small helper functions (for example `create_user`) used by scripts or tests to instantiate models or perform common tasks.

 - `views.py` — Simple page views
	 - Lightweight blueprint that serves top-level pages (e.g., `/` rendering the front dashboard).

 ## Interpreting test results and HTTP status codes

 When running tests or exercising the API (via the Flask test client, curl, or Postman), you will receive HTTP responses with status codes. Below are the common status codes used by this application and what they mean.

 - 200 OK: The request succeeded and the response body contains the requested data (for GET, PATCH when returning the updated resource).
 - 201 Created: A new resource was created successfully (for POST endpoints that create orders or order lines). The response body will include the created resource in JSON.
 - 204 No Content: The request succeeded but there is no response body (used for successful DELETE operations).
 - 400 Bad Request: The server could not process the request because of client-side input errors (missing required fields, invalid JSON, etc.). The response JSON will look like: { "error": "message describing the problem" }.
 - 401 Unauthorized: The user is not authenticated (not logged in). You will usually see this if the session cookie is missing.
 - 403 Forbidden: The user is authenticated but does not have permission to perform the action (for example, only admin can delete orders or only kitchen can update order-line status).
 - 404 Not Found: The requested resource (order, order line, user) does not exist.
 - 500 Internal Server Error: An unexpected server-side error occurred. Check server logs and stack traces for details.

 ### JSON error format

 The API returns errors in a simple JSON shape. Example:

 ```json
 { "error": "customer_id and non-empty lines array required" }
 ```

 ### Tips for quickly spotting success vs failure in tests

 - Look at the HTTP status code first. 2xx codes indicate success; 4xx and 5xx indicate problems.
 - When using the Flask test client in automated tests, assert the expected status code, e.g.:

 ```python
 rv = client.post('/api/orders', json=payload)
 assert rv.status_code == 201
 data = rv.get_json()
 assert 'order_id' in data
 ```

 - When a creation fails during tests you will typically see a 400 with an `error` message explaining which field was missing or invalid.

 ### Postman quick-check workflow

 1. Perform the login POST and confirm you receive a 200 and a session cookie.
 2. POST /api/orders with a valid payload and expect 201. If you get 400, examine the response JSON for the `error` key.
 3. GET /api/orders to confirm the resource was created (200 and JSON list returned).

 If you want, I can also add a small `tests/` example file showing these assertions for your devs to copy into unit tests.<#
Create multiple Azure DevOps work items (type Issue) from an inline list of cards.
Usage:
  # set the PAT in env first (session only)
  $env:AZURE_DEVOPS_PAT = "YOUR_PAT_HERE"

  # run the script (replace organization/project variables inside or pass them as args)
  .\create_azure_issues.ps1

This script expects:
 - $organization (string) e.g. "myorg"
 - $project (string) e.g. "MyProject"
 - $AZURE_DEVOPS_PAT set in the environment
#>

# === Configuration - edit these BEFORE running ===
$organization = "YOUR_ORG"    # <-- replace with your Azure DevOps org
$project = "YOUR_PROJECT"     # <-- replace with your project name
$workItemType = "Issue"       # or "Task" / "Bug" if Issue type is not available
$iterationPath = ""           # optional, e.g. "MyProject\\Sprint 1"
$areaPath = ""                # optional, e.g. "MyProject\\Backend"

# Read PAT from environment (recommended)
$pat = $env:AZURE_DEVOPS_PAT
if (-not $pat) {
    Write-Error "Please set environment variable AZURE_DEVOPS_PAT before running the script."
    exit 1
}
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))

# Cards to create (title, description, tags, optional priority) - edit as needed.
$cards = @(
    @{ title = "Map ORM models to real DB"; description = "Update `app/models.py` to map Employee, Customer, Product, Orders, Order_Line; add to_dict() and relationships."; tags = "backend;models"; priority = 2 },
    @{ title = "Implement Order REST API"; description = "Add GET/POST/PUT/DELETE endpoints for Orders. Create header + lines in POST. Emit socket events."; tags = "backend;api"; priority = 2 },
    @{ title = "Implement OrderLine endpoints + kitchen status updates"; description = "Add POST /api/order_lines and PATCH /api/order_lines/<id>/status for kitchen updates. Ensure role checks."; tags = "backend;kitchen"; priority = 2 },
    @{ title = "Admin user CRUD API"; description = "Add admin-only endpoints to manage users (create/list/update/delete) using password hashing and role validation."; tags = "backend;admin"; priority = 2 },
    @{ title = "Front/Kitchen form handlers to use Orders/OrderLine"; description = "Adapt HTML form handlers to create header+lines and update line statuses as needed."; tags = "frontend;backend"; priority = 3 },
    @{ title = "SocketIO emits compatibility fix"; description = "Remove unsupported broadcast kwarg and ensure socket emits work in test/local environment.", tags = "backend;sockets"; priority = 3 },
    @{ title = "Product price lookup for order line creation"; description = "If unit_price omitted, server should fetch Product.price and store it as the order line unit_price.", tags = "backend;pricing"; priority = 3 },
    @{ title = "Update app README to document files and testing guidance"; description = "Expand `app/app_README.md` to describe all python files in `app/` and include HTTP status code guidance.", tags = "docs;readme"; priority = 4 },
    @{ title = "Add automated unit tests for API"; description = "Add pytest tests for order CRUD and user CRUD using in-memory SQLite and the Flask test client.", tags = "tests;ci"; priority = 1 },
    @{ title = "Export Postman collection for devs"; description = "Create a Postman collection with login, create order, list orders, and update order line status requests.", tags = "devtools;postman"; priority = 3 },
    @{ title = "Add stricter validation & error handling"; description = "Enforce product existence and required fields; return 400 with helpful messages.", tags = "backend;validation"; priority = 2 },
    @{ title = "Add DB seed script for local dev"; description = "Script to seed admin user, sample products and customers for dev/testing.", tags = "devtools;seed"; priority = 3 },
    @{ title = "Create DB migration notes / verify production schema", description = "Check production DB for exact column names and create migrations if schema changes are needed.", tags = "ops;migrations"; priority = 3 },
    @{ title = "Update front-end templates to call JSON API", description = "Replace server-post forms with fetch calls to JSON API and handle socket updates in UI.", tags = "frontend;ui"; priority = 3 },
    @{ title = "Add CI pipeline to run tests and lint", description = "Add GitHub Actions or Azure Pipelines to run tests and basic lint on PRs.", tags = "ci;automation"; priority = 2 },
    @{ title = "Ensure price numerics & JSON serialization", description = "Ensure Decimal/Numeric DB types serialize consistently (two decimals) in API responses.", tags = "backend;formatting"; priority = 3 }
)

# --- helper function to create a single work item ---
function New-AzureDevOpsWorkItem {
    param(
        [string]$org,
        [string]$proj,
        [string]$type,
        [string]$title,
        [string]$description,
        [string]$tags,
        [string]$areaPath,
        [string]$iterationPath,
        [int]$priority
    )

    $uri = "https://dev.azure.com/$org/$proj/_apis/wit/workitems/`$$type?api-version=6.0"

    $ops = @()
    $ops += @{ op = "add"; path = "/fields/System.Title"; value = $title }
    if ($description) {
        $ops += @{ op = "add"; path = "/fields/System.Description"; value = $description }
    }
    if ($tags) {
        $ops += @{ op = "add"; path = "/fields/System.Tags"; value = $tags }
    }
    if ($areaPath) {
        $ops += @{ op = "add"; path = "/fields/System.AreaPath"; value = $areaPath }
    }
    if ($iterationPath) {
        $ops += @{ op = "add"; path = "/fields/System.IterationPath"; value = $iterationPath }
    }
    if ($priority) {
        $ops += @{ op = "add"; path = "/fields/Microsoft.VSTS.Common.Priority"; value = $priority }
    }

    $body = $ops | ConvertTo-Json -Depth 4

    try {
        $resp = Invoke-RestMethod -Method Post -Uri $uri -Headers @{ Authorization = "Basic $base64Auth" } `
            -ContentType "application/json-patch+json" -Body $body
        return $resp
    } catch {
        Write-Error "Failed to create work item '$title': $_"
        return $null
    }
}

# --- main loop creating each card as an Issue ---
Write-Host "Creating $($cards.Count) work items in $organization/$project as type $workItemType ..."
$created = @()
foreach ($c in $cards) {
    $title = $c.title
    $desc = $c.description
    $tags = $c.tags
    $priority = $c.priority

    # Create the item
    $result = New-AzureDevOpsWorkItem -org $organization -proj $project -type $workItemType `
        -title $title -description $desc -tags $tags -areaPath $areaPath -iterationPath $iterationPath -priority $priority

    if ($result) {
        $id = $result.id
        $url = $result._links.html.href
        Write-Host "Created: ID=$id  Title='$title'  URL=$url"
        $created += @{ id = $id; title = $title; url = $url }
    } else {
        Write-Host "Failed to create: $title"
    }
}

Write-Host "Done. Created $($created.Count) work items. Assign parents manually in Azure Boards as needed."

