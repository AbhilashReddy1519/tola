# 5. Viva Prep

If you cannot explain a piece of code, an evaluator will find it. Use this list after each stage. Answers are pointers, not scripts; put them in your own words.

## Django fundamentals

| Question | What a good answer covers |
|---|---|
| Why a custom user model? | Needed a `role` field. Must be set before the first migration because `AUTH_USER_MODEL` is baked into foreign keys. |
| Why `ForeignKey` for Instrument to Business but `OneToOneField` for Inspection to Request? | One business has many instruments; one request has at most one inspection, and the database should enforce that. |
| What does `related_name` do? | Names the reverse accessor, so `business.instruments.all()` reads naturally. |
| Class-based or function-based views, and why? | CBVs for CRUD reuse with mixins (`LoginRequiredMixin`, `RoleRequiredMixin`). Function views only where simpler. |
| What is `select_related` and where did you use it? | Joins foreign keys in one query to avoid N+1. Used on list pages that show instrument and business names. |
| How do migrations work? | `makemigrations` writes the change, `migrate` applies it, and the history table records what ran. |
| Template inheritance? | `base.html` defines blocks; pages extend it. Shared nav rail and fonts live in one place. |
| What does CSRF protect against? | Cross-site forged POSTs. `{% csrf_token %}` in forms and middleware verification. HTMX requests send the token via a header. |

## Design decisions

| Question | What a good answer covers |
|---|---|
| How do you stop one owner opening another owner's instrument? | Every queryset is filtered to the logged-in user's business, and `get_object_or_404` runs on that scoped queryset, so guessing a pk returns 404. |
| Why not set `request.status` in the view? | All changes go through `transition()`, which validates, saves and writes the audit event in one transaction, so no path can skip a rule or leave no trace. |
| Why `transaction.atomic` when issuing a certificate? | The pass transition, certificate creation and certified transition must succeed or fail together. |
| How can a customer trust the certificate? | The PDF and QR only carry a random UUID. The server looks it up and shows the live state, so a copied or edited PDF cannot change what the page says. |
| Why a UUID token instead of the pk? | Sequential ids are guessable and would let someone enumerate certificates. |
| Why recompute pass or fail on the server when HTMX already shows it live? | Client-side values can be edited. The server is the source of truth. |
| Where are the permitted-error limits and why? | One lookup table in `verification/rules.py` so a rule change is a one-line edit. It is a simplified OIML R 76-1 class III set. |

## Metrology domain (be ready for this)

| Question | What a good answer covers |
|---|---|
| What is the verification scale interval *e*? | The value used to classify the instrument and to express permitted errors, set by the manufacturer. |
| Why test accuracy, repeatability and eccentricity? | Accuracy: reads true across the range. Repeatability: gives the same result for the same load. Eccentricity: result does not change with where the load sits on the platform. |
| Why does the permitted error grow with load? | Limits are expressed in multiples of *e* and step up in bands as the load rises. |
| What is the legal basis? | Legal Metrology Act, 2009 and the rules under it. Say you kept fees and validity configurable because they vary by category and state. |

## Honest limitations to volunteer

- Payment is mocked.
- No integration with any government database.
- Permitted-error table is simplified and should be checked against the full standard.
- Single business per owner in the MVP.

Volunteering these before being asked reads as maturity, not weakness.

## Rehearsal

1. Run the 5-minute demo from PRD 1.8 out loud, twice.
2. Pick any view, open it, and explain every line without notes.
3. Break one thing on purpose (for example remove a scope filter), explain the consequence, and restore it.
