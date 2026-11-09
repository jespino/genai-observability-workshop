---
description: Why telemetry needs shared names, and how to read a semantic convention.
part: Foundations
duration: 20 min
---

# Semantic Conventions

OpenTelemetry gives you a way to record an attribute, but not what to call it. One team
records `http.status`, another `status_code`, and a third `response.code`, and now a
dashboard that works for one service shows nothing for the others. Semantic conventions fix
that by defining standard names and meanings for common operations.

## Learning objectives

By the end of this module, you'll be able to:

- [ ] Explain what semantic conventions give you
- [ ] Read a convention's requirement levels and stability
- [ ] Spot telemetry that doesn't follow a convention

## What a convention defines

A semantic convention covers a kind of operation, such as an HTTP request or a database
query, and it defines:

- **Attribute names and meanings**, kept in a shared registry.
- **Span names and kinds**, such as `GET /users/{id}`.
- **Metrics**, with their name, instrument and unit.
- **Events**, for things worth recording on their own.

Here's what an HTTP server span looks like when it follows the HTTP conventions:

| Property | Value |
|---|---|
| Span name | `GET /users/{id}` |
| Span kind | `SERVER` |
| `http.request.method` | `GET` |
| `http.route` | `/users/{id}` |
| `http.response.status_code` | `200` |

Any tool that knows these names can work with this span, whichever language or library
produced it. That's the real value: a dashboard, an alert or a query written once works for
every service. Auto-instrumentation and vendors rely on the same names, which is why they
can offer ready-made views.

## Requirement levels

Not every attribute matters equally, so each one has a level.

| Level | Meaning |
|---|---|
| **Required** | Always set it |
| **Conditionally Required** | Set it when the stated condition holds, such as "if the operation failed" |
| **Recommended** | Set it unless you have a good reason not to |
| **Opt-In** | Leave it off unless the user asks, usually because it's expensive or sensitive |

## Stability

Conventions mature over time, and each element has a stability level. The two you'll meet
are:

- **Stable**: names won't change in a breaking way.
- **Development**: names can still change or disappear between versions.

Keep that second one in mind. It's going to matter in this workshop.

## Cardinality

Cardinality is the number of distinct values of an attribute, and it's the reason that
conventions are careful about what goes where. Every distinct combination of attribute
values on a metric creates a new time series, and each one costs memory. A status code has
a handful of values. A user ID has millions.

So high-cardinality values belong on spans and logs, which are stored one record at a time,
and metrics stick to attributes with few values. It's also why that span is named
`GET /users/{id}` and not `GET /users/1234`.

## Exercise: spot the problems

This one needs no code. A service reports this span for a failed request. List everything
that breaks the conventions described above, and say what could go wrong.

| Property | Value |
|---|---|
| Span name | `GET /users/8841` |
| Span kind | `SERVER` |
| `method` | `get` |
| `http.route` | `/users/{id}` |
| `http.status` | `500` |

The service also has a metric, `http_requests`, with a `user_id` attribute.

> [!HINT]
> There are five problems. Look at the span name, compare the two attribute names with the
> table above, and think about cardinality.

> [!SOLUTION]
> 1. **The span name holds an ID.** Every user gets a different name, so you can't group by
>    it. It should be `GET /users/{id}`.
> 2. **`method` isn't the conventional name.** It should be `http.request.method`.
> 3. **The value `get` is lowercase.** The convention expects the uppercase HTTP method,
>    `GET`.
> 4. **`http.status` isn't the conventional name.** It should be
>    `http.response.status_code`, and a dashboard using that name won't see this span.
> 5. **`user_id` on a metric is a cardinality problem.** One time series per user can take
>    your metrics store down. Keep it on spans.

## Key takeaways

- Conventions are what make telemetry from different services and tools comparable.
- Requirement levels tell you what to set, from Required down to Opt-In.
- Stability tells you how far you can rely on a name.
- Keep high-cardinality values away from metrics.

Next, we'll build the application that we're going to observe.
