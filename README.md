# DAY 4 — ASYNC, MIDDLEWARE & MODULAR FASTAPI

**Name:** Polagani Harinadh Babu
**Date:** 29-10-2026
**Technology:** Python, FastAPI, asyncio, Middleware, Dependency Injection, APIRouter

## Task A — Async: Sequential vs Concurrent Execution

### Objective

To write three coroutines simulating independent I/O operations, compare sequential execution with `asyncio.gather()`, and explain their execution time.

### Code

```python
import asyncio
import time


async def fetch_data(name, delay):
    await asyncio.sleep(delay)
    return f"{name} completed"


async def sequential_execution():
    start = time.perf_counter()

    profile = await fetch_data("Profile", 1)
    alerts = await fetch_data("Alerts", 1)
    feed = await fetch_data("Feed", 1)

    print(profile)
    print(alerts)
    print(feed)

    print("Sequential time:",
          round(time.perf_counter() - start, 2), "seconds")


async def concurrent_execution():
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch_data("Profile", 1),
        fetch_data("Alerts", 1),
        fetch_data("Feed", 1)
    )

    print(results)
    print("Concurrent time:",
          round(time.perf_counter() - start, 2), "seconds")


async def main():
    print("Sequential Execution")
    await sequential_execution()

    print("\nConcurrent Execution")
    await concurrent_execution()


asyncio.run(main())
```

### Expected result

- Sequential execution: approximately 3 seconds.
- Concurrent execution: approximately 1 second.

### Explanation

Sequential execution waits for each coroutine to finish before starting the next one. Therefore, three independent operations taking one second each require approximately three seconds.

`asyncio.gather()` allows independent awaitables to overlap their waiting time. Therefore, the total execution time approaches the longest individual delay, plus overhead.

**Conclusion:** `asyncio.gather()` is useful for independent I/O-bound operations. Timeouts and exception handling should be considered in real applications.

---

## Task B — Async FastAPI Endpoint

### Objective

To create an asynchronous FastAPI endpoint and explain why blocking operations should be avoided.

### Code — `main.py`

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()


@app.get("/status")
async def status():
    await asyncio.sleep(1)

    return {
        "status": "ready",
        "message": "Async endpoint executed successfully"
    }
```

### Run the application

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

Open the endpoint:

`http://127.0.0.1:8000/status`

API documentation:

`http://127.0.0.1:8000/docs`

### Expected response

```json
{
  "status": "ready",
  "message": "Async endpoint executed successfully"
}
```

### Explanation

An asynchronous route uses `async def` and `await` to work with asynchronous operations. While the coroutine waits for I/O, the event loop can schedule other ready tasks.

`asyncio.sleep()` provides a safe demonstration of a non-blocking wait.

Using `time.sleep()` inside an asynchronous handler blocks the event-loop thread and can slow down unrelated requests. Real network and database operations should use compatible asynchronous clients when appropriate.

**Conclusion:** Asynchronous programming improves concurrency for I/O-bound workloads, but it does not automatically make CPU-intensive calculations faster.

---

## Task C — Middleware and Request Timing

### Objective

To implement timing middleware that measures request processing time and adds an `X-Process-Time` response header.

### Code

```python
from time import perf_counter
from fastapi import FastAPI, Request
import asyncio

app = FastAPI()


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = perf_counter()

    response = await call_next(request)

    elapsed = perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"

    return response


@app.get("/test")
async def test_endpoint():
    await asyncio.sleep(0.1)

    return {"message": "Request completed successfully"}
```

### Run and test

```bash
uvicorn main:app --reload
```

Open:

`http://127.0.0.1:8000/test`

Check the response headers using the browser developer tools or:

```bash
curl -i http://127.0.0.1:8000/test
```

### Expected response body

```json
{
  "message": "Request completed successfully"
}
```

The response headers should include an entry similar to:

```text
X-Process-Time: 0.101234
```

The exact value will vary.

### Explanation

Middleware wraps request and response processing. It can execute before a route handler and after the response is produced.

The timing middleware records the starting time, awaits the next processing layer, calculates the elapsed time, and adds it to the response header.

This information helps developers diagnose performance issues and monitor request processing.

In production, request logging should avoid exposing passwords, bearer tokens, authorization headers, or session cookies.

**Conclusion:** Middleware provides a reusable way to handle cross-cutting concerns such as timing, logging, request IDs, and CORS.

---

## Task D — Dependencies and Sub-dependencies

### Objective

To create reusable pagination and current-user dependencies, demonstrate a sub-dependency, and explain production authentication.

### Code — `dependencies.py`

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException


def common_paging(skip: int = 0, limit: int = 20):
    return {
        "skip": max(skip, 0),
        "limit": min(max(limit, 1), 100)
    }


Paging = Annotated[dict, Depends(common_paging)]


# Demonstration only.
# A real application must validate credentials securely.
DEMO_USERS = {
    "demo-viewer-token": {
        "id": 1,
        "role": "viewer"
    },
    "demo-admin-token": {
        "id": 2,
        "role": "admin"
    }
}


def get_current_user(
    authorization: Annotated[str | None, Header()] = None
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    token = authorization.removeprefix("Bearer ").strip()
    user = DEMO_USERS.get(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    return user


def require_admin(
    user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )

    return user
```

### Code — `main.py`

```python
from typing import Annotated
from fastapi import FastAPI, Depends
from dependencies import (
    Paging,
    get_current_user,
    require_admin
)

app = FastAPI()


@app.get("/products")
def list_products(paging: Paging):
    return {
        "skip": paging["skip"],
        "limit": paging["limit"],
        "products": []
    }


@app.get("/users/me")
def current_user(
    user=Depends(get_current_user)
):
    return user


@app.get("/admin")
def admin_area(
    user=Depends(require_admin)
):
    return {
        "message": "Welcome to the admin area",
        "user_id": user["id"]
    }
```

### Sample requests

Pagination:

```bash
curl "http://127.0.0.1:8000/products?skip=0&limit=10"
```

Current user:

```bash
curl -H "Authorization: Bearer demo-viewer-token" \
http://127.0.0.1:8000/users/me
```

Admin route with an admin token:

```bash
curl -H "Authorization: Bearer demo-admin-token" \
http://127.0.0.1:8000/admin
```

Admin route with a viewer token should return HTTP `403 Forbidden`.

### Explanation

Dependency injection allows FastAPI to call a dependency and pass its result to a route. Dependencies can centralize pagination, authentication, database sessions, configuration, and validation.

A sub-dependency is a dependency that relies on another dependency. In this example, `require_admin()` depends on `get_current_user()`.

A viewer who is authenticated but does not have administrator permissions must receive HTTP `403`. Missing or invalid authentication credentials should receive HTTP `401`.

The token mapping above is only a demonstration. Production authentication must validate signed credentials or tokens securely and obtain roles and permissions from trusted server-side data. A client-supplied role must never be trusted.

Yield-based dependencies can also initialize and clean up database sessions, including closing sessions when request handling fails.

**Conclusion:** `Depends()` improves code reuse and organization. Authentication and authorization checks must be explicitly enforced.

---

## Task E — APIRouter and Modular Application Structure

### Objective

To divide endpoints into separate router modules, register them with prefixes and tags, and verify the routes in FastAPI documentation.

### Project structure

```text
day4_fastapi/
│
├── main.py
├── dependencies.py
└── routers/
    ├── __init__.py
    ├── products.py
    └── users.py
```

Create an empty `__init__.py` file inside the `routers` folder.

### File 1 — `routers/products.py`

```python
from fastapi import APIRouter, Depends
from dependencies import Paging

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/")
def list_products(paging: Paging):
    return {
        "skip": paging["skip"],
        "limit": paging["limit"],
        "products": [
            {"id": 1, "name": "Pen"},
            {"id": 2, "name": "Notebook"}
        ]
    }


@router.get("/{product_id}")
def get_product(product_id: int):
    return {
        "id": product_id,
        "name": "Sample product"
    }
```

### File 2 — `routers/users.py`

```python
from fastapi import APIRouter, Depends
from dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/me")
def get_profile(user=Depends(get_current_user)):
    return user


@router.get("/admin")
def admin_profile(user=Depends(require_admin)):
    return {
        "message": "Admin access granted",
        "user_id": user["id"]
    }
```

### File 3 — `main.py`

```python
from fastapi import FastAPI
from routers.products import router as products_router
from routers.users import router as users_router

app = FastAPI(
    title="Day 4 FastAPI Assignment",
    description="Async, middleware, dependencies and routers"
)

app.include_router(
    products_router,
    prefix="/api/v1"
)

app.include_router(
    users_router,
    prefix="/api/v1"
)


@app.get("/status", tags=["health"])
async def status():
    return {"status": "ready"}
```

### Run the project

Run this command from the `day4_fastapi` directory:

```bash
uvicorn main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

### Routes to verify

| Method | Route                           | Purpose                  |
| ------ | ------------------------------- | ------------------------ |
| GET    | `/status`                       | Check application status |
| GET    | `/api/v1/products/`             | List products            |
| GET    | `/api/v1/products/{product_id}` | Retrieve a product       |
| GET    | `/api/v1/users/me`              | Retrieve current user    |
| GET    | `/api/v1/users/admin`           | Admin-only route         |

### Explanation

`APIRouter` groups related endpoints into reusable modules. Prefixes organize URL paths, while tags group operations in the generated API documentation.

Separating routes, schemas, services, and dependencies makes the project easier to maintain and test. Explicit router registration also helps prevent circular imports and keeps the application organized.

**Conclusion:** Modular FastAPI applications are easier to extend, debug, and maintain than applications with every endpoint inside one large `main.py` file.

---

## Task F — Lifespan and Background Tasks

### Objective

To demonstrate application startup and shutdown, explain background task execution, and distinguish non-critical work from durable jobs.

### Code — `main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.ready = True
    logger.info("Application started")

    yield

    # Shutdown
    app.state.ready = False
    logger.info("Application stopped")


app = FastAPI(lifespan=lifespan)


def write_audit_log(message: str):
    logger.info("Audit event: %s", message)


@app.get("/status")
async def status():
    return {
        "ready": app.state.ready
    }


@app.post("/orders")
def create_order(background_tasks: BackgroundTasks):
    background_tasks.add_task(
        write_audit_log,
        "Order created"
    )

    return {
        "message": "Order accepted"
    }
```

### Run and test

```bash
uvicorn main:app --reload
```

Check application readiness:

```bash
curl http://127.0.0.1:8000/status
```

Schedule the audit log:

```bash
curl -X POST http://127.0.0.1:8000/orders
```

Expected response:

```json
{
  "message": "Order accepted"
}
```

The audit message should appear in the application logs after the response is returned.

### Explanation

The FastAPI lifespan context manager handles application startup and shutdown. It is useful for initializing and cleaning up shared resources such as database connection pools and clients.

`BackgroundTasks` is suitable for small, non-critical, in-process follow-up work, such as sending a simple notification or writing an audit message.

However, background tasks run in the application process and are not durable. If the server stops before a task completes, the work can be lost.

For important invoice processing, financial settlement, long-running jobs, or work requiring retries, use a persistent job queue and a separate worker. Such systems should include monitoring and idempotency where appropriate.

**Conclusion:** Use lifespan for resource management, `BackgroundTasks` for small follow-up operations, and a durable queue for critical work.

---

## Task G — Reflection, Tests, Edge Cases and Architecture

### 1. Run instructions

Install the required dependencies:

```bash
pip install fastapi uvicorn pytest httpx
```

Run the application:

```bash
uvicorn main:app --reload
```

Open the API documentation:

`http://127.0.0.1:8000/docs`

Run automated tests:

```bash
pytest -v
```

### 2. Sample tests

Create a file named `test_main.py`:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_status():
    response = client.get("/status")
    assert response.status_code == 200


def test_list_products():
    response = client.get("/api/v1/products/")
    assert response.status_code == 200


def test_get_product():
    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_user_requires_authentication():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_admin_rejects_viewer():
    response = client.get(
        "/api/v1/users/admin",
        headers={
            "Authorization": "Bearer demo-viewer-token"
        }
    )
    assert response.status_code == 403


def test_admin_accepts_admin():
    response = client.get(
        "/api/v1/users/admin",
        headers={
            "Authorization": "Bearer demo-admin-token"
        }
    )
    assert response.status_code == 200
```

**Note:** These tests apply to the modular project created in Task E, with the same `dependencies.py` implementation from Task D and the `/status` endpoint shown in Task E.

### 3. Edge cases to consider

1. **Async execution:** One coroutine may take longer than the others. Total concurrent time depends on the slowest operation and overhead.
2. **Timeouts:** A slow external service should not make the request wait indefinitely.
3. **Exceptions:** If one coroutine in `asyncio.gather()` fails, the exception is propagated by default. Partial-result handling must be designed deliberately.
4. **Blocking operations:** Avoid `time.sleep()` and blocking I/O in asynchronous handlers. Consider a process pool or separate worker for CPU-intensive work.
5. **Authorization:** Missing or invalid credentials should return HTTP `401`; an authenticated user without permission should return HTTP `403`.
6. **Database cleanup:** Use yield-based dependencies to close database sessions even when request processing fails.
7. **Middleware:** Verify middleware order and interactions. Redact credentials and other sensitive information from logs.
8. **CORS:** Configure trusted frontend origins, required methods, and headers explicitly. Avoid wildcard origins when credentials are enabled.
9. **Background tasks:** Use a durable queue with retries for critical work that must survive process restarts.
10. **Pagination:** Validate pagination values and limit excessively large page sizes.

### 4. Architecture choices

- **Async/await:** Used for I/O-bound operations that support asynchronous execution.
- **`asyncio.gather()`:** Used to overlap independent asynchronous operations.
- **Middleware:** Used for reusable request timing and response metadata.
- **`Depends()`:** Used to reuse pagination and authentication logic.
- **Sub-dependencies:** Used to build authorization checks on top of current-user authentication.
- **`APIRouter`:** Used to separate products and user endpoints.
- **Lifespan:** Used to manage application startup and shutdown.
- **`BackgroundTasks`:** Used for small, non-critical follow-up work.
- **Persistent queue:** Recommended for critical tasks requiring retries and durability.

### 5. What I learned

In Day 4, I learned how Python asynchronous programming works with `async def`, `await`, coroutines, the event loop, and `asyncio.gather()`. I understood the difference between blocking and non-blocking operations and why CPU-intensive tasks may require a process pool or separate worker.

I also learned how to create asynchronous FastAPI endpoints, implement timing middleware, configure CORS, and use dependency injection for reusable logic and authorization. I practiced organizing endpoints with `APIRouter`, managing application resources through lifespan, and choosing between in-process background tasks and persistent job queues.

### 6. Interview questions and answers

**Q1. What is a coroutine?**

A coroutine is an asynchronous unit of work defined using `async def`. Calling it creates a coroutine object.

**Q2. What does `await` do?**

`await` suspends the current coroutine until the awaited operation completes, allowing other tasks to run.

**Q3. What is the event loop?**

The event loop schedules asynchronous tasks and coordinates I/O operations and callbacks.

**Q4. What is the difference between `asyncio.gather()` and sequential awaits?**

`asyncio.gather()` overlaps independent awaitables, whereas sequential awaits generally wait for each operation one by one.

**Q5. Why is `time.sleep()` risky in asynchronous code?**

It blocks the current thread and prevents the event loop from scheduling other work on that thread.

**Q6. What is middleware?**

Middleware is a layer around request and response processing used for timing, logging, request IDs, and other cross-cutting concerns.

**Q7. What is CORS?**

CORS is a browser-enforced policy controlling whether a page from one origin can read responses from another origin. It is not authentication.

**Q8. What does `Depends()` do?**

It declares a dependency that FastAPI resolves and injects into a route or another dependency.

**Q9. What is `APIRouter`?**

`APIRouter` organizes related API endpoints into reusable modules with prefixes and tags.

**Q10. When should we use `BackgroundTasks`?**

Use it for small, in-process follow-up work after a response, not durable jobs requiring retries.

**Q11. What is lifespan used for?**

Lifespan initializes and cleans up shared application resources at startup and shutdown.

**Q12. How should critical background work be handled?**

Use a persistent job queue and worker with retries, monitoring, and appropriate idempotency controls.

### 7. GitHub submission

**Repository name:** PP_DAY4

**Recommended repository structure:**

```text
DAY4_ASYNC_MIDDLEWARE_FASTAPI/
├── README.md
├── main.py
├── dependencies.py
├── test_main.py
└── routers/
    ├── __init__.py
    ├── products.py
    └── users.py
```

**Git commands:**

```bash
git init
git add .
git commit -m "Complete Day 4 FastAPI assignment"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the URL of your actual repository. If the Git repository is already initialized and the remote already exists, do not repeat those setup commands.

**Assignment submission link:** [https://forms.gle/UDtjdsHGjrW7qyi87](https://forms.gle/UDtjdsHGjrW7qyi87)

**Final note:** Run the tests and verify `/docs` before submitting. The code samples are organized by task; use the modular implementation in Tasks D–F consistently when combining them into the final project.
