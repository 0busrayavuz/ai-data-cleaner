import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import text
from backend.database import run_light_migrations

@patch("backend.database.SQLALCHEMY_DATABASE_URL", "sqlite:///./test.db")
@patch("backend.database.engine")
@patch("backend.database.inspect")
def test_migration_sqlite_skips_postgres_path(mock_inspect, mock_engine):
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    mock_inspector = MagicMock()
    mock_inspect.return_value = mock_inspector

    mock_inspector.has_table.return_value = True
    mock_inspector.get_columns.return_value = [{"name": "id"}]

    run_light_migrations()

    # In SQLite, it should not execute any ALTER TABLE ALTER COLUMN or ADD CONSTRAINT queries.
    executed_sqls = [str(call[0][0].text) for call in mock_conn.execute.call_args_list]
    for sql in executed_sqls:
        assert "ADD CONSTRAINT" not in sql
        assert "ALTER COLUMN" not in sql
        assert "DELETE FROM" not in sql


@patch("backend.database.SQLALCHEMY_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/db")
@patch("backend.database.engine")
@patch("backend.database.inspect")
def test_migration_postgres_adds_user_id_column(mock_inspect, mock_engine):
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    mock_inspector = MagicMock()
    mock_inspect.return_value = mock_inspector

    # Table exists, but datasets is missing "user_id"
    mock_inspector.has_table.side_effect = lambda t: t in ["datasets", "users"]
    mock_inspector.get_columns.side_effect = lambda t: [
        {"name": "id"},
        {"name": "filename"},
    ] if t == "datasets" else []

    run_light_migrations()

    executed_sqls = [str(call[0][0].text) for call in mock_conn.execute.call_args_list]
    assert any("ALTER TABLE datasets ADD COLUMN user_id" in sql for sql in executed_sqls)
    # Since column was just added, it starts NULL, but no DELETE/UPDATE should target user_id orphans
    assert not any("DELETE FROM datasets" in sql for sql in executed_sqls)


@patch("backend.database.SQLALCHEMY_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/db")
@patch("backend.database.engine")
@patch("backend.database.inspect")
def test_migration_postgres_resolves_orphans_with_update(mock_inspect, mock_engine):
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    mock_inspector = MagicMock()
    mock_inspect.return_value = mock_inspector

    # user_id column exists, but user FK is missing
    mock_inspector.has_table.side_effect = lambda t: t in ["datasets", "users"]
    mock_inspector.get_columns.side_effect = lambda t: [
        {"name": "id", "nullable": True},
        {"name": "user_id", "nullable": True},
    ] if t == "datasets" else []
    mock_inspector.get_foreign_keys.return_value = [] # no FKs

    # Mock DB query results
    def mock_execute(sql, *args, **kwargs):
        sql_str = str(sql.text).strip().lower()
        res = MagicMock()
        if "count(*) from datasets where user_id is null" in sql_str:
            res.scalar.return_value = 3
        elif "count(*) from users" in sql_str:
            res.scalar.return_value = 1
        else:
            res.scalar.return_value = 0
        return res
    mock_conn.execute.side_effect = mock_execute

    run_light_migrations()

    executed_sqls = [str(call[0][0].text) for call in mock_conn.execute.call_args_list]

    # Verify that UPDATE was used instead of DELETE for invalid user_ids
    assert any("UPDATE datasets SET user_id = NULL" in sql for sql in executed_sqls)
    assert not any("DELETE FROM datasets WHERE user_id" in sql for sql in executed_sqls)

    # Verify FK constraint is added
    assert any("ADD CONSTRAINT fk_datasets_user" in sql for sql in executed_sqls)

    # Verify orphan assignment to single user and NOT NULL enforcement
    assert any("UPDATE datasets SET user_id = (SELECT id FROM users LIMIT 1) WHERE user_id IS NULL" in sql for sql in executed_sqls)
    assert any("ALTER TABLE datasets ALTER COLUMN user_id SET NOT NULL" in sql for sql in executed_sqls)


@patch("backend.database.SQLALCHEMY_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/db")
@patch("backend.database.engine")
@patch("backend.database.inspect")
def test_migration_postgres_multi_users_skips_not_null(mock_inspect, mock_engine):
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    mock_inspector = MagicMock()
    mock_inspect.return_value = mock_inspector

    mock_inspector.has_table.side_effect = lambda t: t in ["datasets", "users"]
    mock_inspector.get_columns.side_effect = lambda t: [
        {"name": "id", "nullable": True},
        {"name": "user_id", "nullable": True},
    ] if t == "datasets" else []
    mock_inspector.get_foreign_keys.return_value = []

    def mock_execute(sql, *args, **kwargs):
        sql_str = str(sql.text).strip().lower()
        res = MagicMock()
        if "count(*) from datasets where user_id is null" in sql_str:
            res.scalar.return_value = 5
        elif "count(*) from users" in sql_str:
            res.scalar.return_value = 3  # Multiple users
        else:
            res.scalar.return_value = 0
        return res
    mock_conn.execute.side_effect = mock_execute

    run_light_migrations()

    executed_sqls = [str(call[0][0].text) for call in mock_conn.execute.call_args_list]

    # With multiple users, we should skip assigning and skip NOT NULL to protect data ownership
    assert not any("LIMIT 1" in sql and "WHERE user_id IS NULL" in sql for sql in executed_sqls)
    assert not any("SET NOT NULL" in sql for sql in executed_sqls)


@patch("backend.database.SQLALCHEMY_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/db")
@patch("backend.database.engine")
@patch("backend.database.inspect")
def test_migration_postgres_zero_users_skips_not_null(mock_inspect, mock_engine):
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    mock_inspector = MagicMock()
    mock_inspect.return_value = mock_inspector

    mock_inspector.has_table.side_effect = lambda t: t in ["datasets", "users"]
    mock_inspector.get_columns.side_effect = lambda t: [
        {"name": "id", "nullable": True},
        {"name": "user_id", "nullable": True},
    ] if t == "datasets" else []
    mock_inspector.get_foreign_keys.return_value = []

    def mock_execute(sql, *args, **kwargs):
        sql_str = str(sql.text).strip().lower()
        res = MagicMock()
        if "count(*) from datasets where user_id is null" in sql_str:
            res.scalar.return_value = 5
        elif "count(*) from users" in sql_str:
            res.scalar.return_value = 0  # No users
        else:
            res.scalar.return_value = 0
        return res
    mock_conn.execute.side_effect = mock_execute

    run_light_migrations()

    executed_sqls = [str(call[0][0].text) for call in mock_conn.execute.call_args_list]

    # No users -> cannot determine owner, must skip NOT NULL
    assert not any("SET NOT NULL" in sql for sql in executed_sqls)


def test_live_postgresql_migration():
    # Only run if SQLALCHEMY_DATABASE_URL is a PostgreSQL database
    from backend.database import SQLALCHEMY_DATABASE_URL, engine
    if not SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        pytest.skip("SQLAlchemy URL is not PostgreSQL; skipping live database migration test.")

    import uuid
    from sqlalchemy import inspect
    
    # Generate unique test schema name to keep test completely isolated
    schema_name = f"temp_mig_test_{uuid.uuid4().hex[:12]}"
    
    # Setup test schema
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA {schema_name}"))
        
    try:
        # Create tables in their old schema state
        with engine.begin() as conn:
            conn.execute(text(f"SET search_path TO {schema_name}"))
            
            conn.execute(text(
                "CREATE TABLE users ("
                "  id SERIAL PRIMARY KEY,"
                "  email VARCHAR UNIQUE NOT NULL,"
                "  hashed_password VARCHAR NOT NULL"
                ")"
            ))
            
            conn.execute(text(
                "CREATE TABLE datasets ("
                "  id SERIAL PRIMARY KEY,"
                "  filename VARCHAR NOT NULL,"
                "  format VARCHAR NOT NULL"
                ")"
            ))
            
            conn.execute(text(
                "CREATE TABLE cleaning_logs ("
                "  id SERIAL PRIMARY KEY,"
                "  dataset_id INTEGER NOT NULL,"
                "  module VARCHAR,"
                "  column_name VARCHAR,"
                "  method VARCHAR,"
                "  details TEXT"
                ")"
            ))
            
            # Insert some dummy records
            conn.execute(text("INSERT INTO datasets (filename, format) VALUES ('test1.csv', 'csv')"))
            conn.execute(text("INSERT INTO datasets (filename, format) VALUES ('test2.csv', 'csv')"))
            
        real_begin = engine.begin
        
        def mock_begin():
            class CustomCM:
                def __enter__(self):
                    self.cm = real_begin()
                    self.conn = self.cm.__enter__()
                    self.conn.execute(text(f"SET search_path TO {schema_name}"))
                    return self.conn
                def __exit__(self, exc_type, exc_val, exc_tb):
                    return self.cm.__exit__(exc_type, exc_val, exc_tb)
            return CustomCM()
            
        with patch.object(engine, "begin", side_effect=mock_begin):
            from sqlalchemy import inspect as real_inspect
            
            def mock_inspect(bind):
                class SchemaInspector:
                    def __init__(self, inspector):
                        self.inspector = inspector
                    def has_table(self, table_name, schema=None):
                        return self.inspector.has_table(table_name, schema=schema_name)
                    def get_columns(self, table_name, schema=None):
                        return self.inspector.get_columns(table_name, schema=schema_name)
                    def get_foreign_keys(self, table_name, schema=None):
                        return self.inspector.get_foreign_keys(table_name, schema=schema_name)
                return SchemaInspector(real_inspect(bind))
                
            with patch("backend.database.inspect", side_effect=mock_inspect):
                run_light_migrations()
                
        # Verify schema in our test schema
        with engine.begin() as conn:
            conn.execute(text(f"SET search_path TO {schema_name}"))
            
            inspector = inspect(engine)
            d_cols = {c["name"] for c in inspector.get_columns("datasets", schema=schema_name)}
            assert "user_id" in d_cols
            assert "original_filename" in d_cols
            assert "status" in d_cols
            
            fks = inspector.get_foreign_keys("datasets", schema=schema_name)
            has_user_fk = any(
                fk["referred_table"] == "users" and "user_id" in fk["constrained_columns"]
                for fk in fks
            )
            assert has_user_fk
            
            # Verify datasets table has 2 rows (no rows deleted!)
            row_count = conn.execute(text("SELECT COUNT(*) FROM datasets")).scalar()
            assert row_count == 2
            
    finally:
        with engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
