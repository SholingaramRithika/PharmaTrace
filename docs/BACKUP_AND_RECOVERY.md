# Backup and Recovery
> Commands below follow the Neo4j 5 Operations Manual conventions but were **not executed** in the authoring sandbox. Confirm exact syntax in <https://neo4j.com/docs/operations-manual/current/> for your version.

## Local (Neo4j Desktop / Community)
Community Edition supports **offline** dump and load (the database must be stopped):
```powershell
# stop the DBMS in Neo4j Desktop first, then use the neo4j-admin shipped with that DBMS (open its terminal from Desktop)
neo4j-admin database dump neo4j --to-path=C:\backups\pharmatrace
# restore into a stopped DBMS
neo4j-admin database load neo4j --from-path=C:\backups\pharmatrace --overwrite-destination=true
```
Online (hot) backup is an **Enterprise** feature (`neo4j-admin database backup`). Aura provides managed snapshots/restore, with retention depending on plan.

## Rebuild-from-source recovery (works on every edition)
Because the dataset is deterministic, the fastest recovery for this project is:
```powershell
python database\setup_db.py reset --confirm   # optional wipe (local only)
python database\setup_db.py all               # schema + data + validation
```
Only data created interactively (`TEST-*` records) is lost; those are disposable by design.

## Recommended practice for a real deployment
Scheduled backups to separate storage, periodic restore drills, retention policy, encrypted backup storage, and monitoring of backup success. None of this is implemented here beyond the commands above.
