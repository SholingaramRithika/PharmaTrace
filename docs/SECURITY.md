# Security
## Implemented in this project
| Control | Implementation |
|---|---|
| No secrets in code/ZIP | `.env` git-ignored; `.env.example` has placeholders; ZIP contains no `.env` |
| Credentials server-side only | Frontend knows only `VITE_API_URL`; Neo4j credentials are read by the backend (`pydantic-settings`, `SecretStr`) |
| Injection resistance | All values passed as Cypher parameters; labels/relationship types come from allowlists; node ids validated by regex; Lab runs only allowlisted templates with validated parameters (offline tests include injection-style inputs) |
| Safe writes | CRUD/Lab writes limited to `TEST-*` + `isTestRecord`; disabled unless `ENABLE_WRITES=true`; optional `X-Admin-Token` |
| CORS | Restricted to `CORS_ORIGINS`, methods and headers whitelisted, no credentials |
| Error hygiene | Consistent envelope; database errors mapped to generic messages (no stack traces, no connection strings, no passwords in responses/logs; tested) |
| Production surface | `/docs` and OpenAPI disabled when `APP_ENV=production` |
| Transport | Local `bolt://` (loopback). Production must use encrypted `neo4j+s://` (Aura enforces TLS); host the API over HTTPS (Render/Vercel do) |

## Neo4j-side concepts (documented, partly edition-specific)
Authentication is built in (native users). Role-based access control with fine-grained privileges and richer auth providers are described in the Operations Manual as Enterprise/Aura capabilities; Community offers basic authentication. Encryption in transit uses TLS; encryption at rest depends on disk/cloud configuration. Use a least-privilege database user for the API in production.

## Known limitations / production hardening
* No end-user authentication/authorisation in the website (read endpoints are public to any allowed origin). Add an identity provider and per-role authorisation before any real use.
* No rate limiting or request-size limits beyond FastAPI defaults; add a gateway/WAF.
* `X-Admin-Token` is a shared secret, not a user model; keep `ENABLE_WRITES=false` on public deployments.
* Lab EXPLAIN/PROFILE output reveals schema details; acceptable for synthetic data only.
* Dependency pins are as tested; run `pip-audit` / `npm audit` before deployment (not run here).
