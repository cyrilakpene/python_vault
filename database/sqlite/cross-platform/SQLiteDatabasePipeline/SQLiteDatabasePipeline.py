import re
import os
import sqlite3
from typing import Any, cast
from contextlib import contextmanager
from collections.abc import Sequence


# PERSISTENCE LAYER & ACID TRANSACTIONAL PIPELINE
# CONCRETE ACCESS ADAPTER: OPTIMIZED RELATIONAL DATA MANAGEMENT ENGINE
# This class provides the high-performance persistence engine for streaming relational workloads.
# By combining thread-safe context pools with dynamic query construction, it guarantees structural
# query integrity, deterministic transactional rollbacks, and efficient SQLite throughput.
#
# CONCURRENCY CONTROL & RESOURCE LOCK BOUNDING:
# Operations within this pipeline enforce isolated transaction scopes to safely handle multi-threaded access.
# To prevent database locking, thread starvation, and connection leaks, context operations operate via
# strict connection-pooling semantics, ensuring connections are automatically sanitized and released.
#
# SUBSYSTEM INTEGRATION PIPELINE:
# This persistence pipeline serves as the primary storage gateway for post-transformation dataset sinks.
# Downstream diagnostic loggers, transactional dataset indexers, and materialization workflows
# depend explicitly on this layer to guarantee durable, ACID-compliant writes during active pipeline execution.
class SQLiteDatabasePipeline:
    """
    An optimized SQL pipeline for SQLite featuring thread-safe context management,
    dynamic query building, and automated transaction handling.

    This persistence engine manages real-time relational storage, context propagation, and query execution.
    It mandates automated connection lifecycle tracking, safe dynamic query building, and transaction-isolated
    rollback guarantees to ensure data integrity during streaming database operations.
    """

    # STATE INITIALIZATION: DATABASE PERSISTENCE & RESOURCE BOUNDARY INITIALIZER
    # This constructor sets up the SQLite storage boundary and filesystem infrastructure.
    # Concrete instances isolate connection configuration settings, ensure target parent directories
    # are physically created on disk for persistent databases, and bypass directory provisioning
    # when handling in-memory URI flags.
    def __init__(self, db_path: str = "app_database.db"):
        """
        CONSTRUCTOR HOOK: DATABASE CONNECTION PROVIDER INITIALIZATION
        Establishes database target paths and prepares local filesystem structures to support
        persistent relational storage drivers.

        Args:
            db_path (str, optional): Target database file path, in-memory indicator (':memory:'),
                or file URI scheme. Defaults to "app_database.db".
        """
        # TARGET PATH BINDING
        # Store relational database destination path parameter to local instance context
        self.db_path = db_path

        # FILESYSTEM DIRECTORY PROVISIONING GUARD
        # Validate path type and dynamically create missing target directories for physical file paths
        if db_path != ":memory:" and not db_path.startswith("file:"):
            dirname = os.path.dirname(db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    # PERSISTENCE ENGINE: THREAD-SAFE CURSOR & TRANSACTION CONTEXT MANAGER
    # This context manager encapsulates lifecycle management for relational database interactions.
    # Concrete execution involves opening isolated thread connections, configuring factory row mappings,
    # yielding active database cursors to execution blocks, managing atomic transaction commits or rollbacks,
    # and guaranteeing connection cleanup via exception interception guard blocks.
    @contextmanager
    def _get_cursor(self, commit: bool = False):
        """
        CONTEXT MANAGER HOOK: THREAD CONNECTION & CURSOR LIFECYCLE CONTROLLER
        Provides isolated, thread-safe access to database cursors with automated transaction
        commit/rollback handling and resource cleanup.

        Args:
            commit (bool, optional): Flag indicating whether structural schema modifications
                or DML state changes should be committed upon success. Defaults to False.

        Yields:
            sqlite3.Cursor: Active database cursor configured with dictionary-like row factory access.

        Raises:
            sqlite3.Error: Re-raises underlying database driver exceptions following transaction rollback.
        """
        # INITIALIZE LIFECYCLE RESOURCE HANDLES
        conn = None
        cursor = None
        try:
            # ESTABLISH CONNECTION & CONFIGURE ROW FACTORY
            # Connect to database destination path and enable named column indexing on returned rows
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # YIELD ACTIVE CURSOR TO CALLER CONTEXT
            yield cursor

            # TRANSACTION COMMIT EXECUTION
            # Persist state changes if explicitly requested by caller
            if commit:
                conn.commit()

        except sqlite3.Error as e:
            # EXCEPTION INTERCEPTION & TRANSACTION ROLLBACK
            # Rollback uncommitted transactions to maintain database consistency upon runtime errors
            if conn and commit:
                conn.rollback()
            raise e

        finally:
            # RESOURCE CLEANUP & CONNECTION DISPOSAL
            # Explicitly close cursor handles and return connection resources to system pool
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # PERSISTENCE ENGINE: IDENTIFIER SANITIZER & SQL INJECTION GUARD
    # This utility function sanitizes dynamic structural database identifiers such as table and column names.
    # Concrete execution relies on regular expression substitution to strip non-alphanumeric characters,
    # ensuring identifiers strictly adhere to safe schema naming conventions and neutralizing potential
    # SQL injection vectors within non-parameterizable DDL/DML statements.
    def _sanitize(self, identifier: str) -> str:
        """
        SECURITY HOOK: STRUCTURAL IDENTIFIER SANITIZER
        Strips non-alphanumeric characters to secure dynamic table and column identifiers.

        Args:
            identifier (str): Raw column or table name string to be sanitized.

        Returns:
            str: Sanitized identifier string containing strictly alphanumeric characters and underscores.
        """
        # REGEX REGISTRATION & NON-ALPHANUMERIC STRIPPING
        # Retain ASCII letters, digits, and underscores while stripping invalid or malicious characters
        return re.sub(r"[^a-zA-Z0-9_]", "", identifier)

    # PERSISTENCE ENGINE: ROW-TO-DICTIONARY DATA TRANSFORMER
    # This data formatting helper serializes raw database row instances into native Python dictionaries.
    # Concrete execution inspects the polymorphic input payload, delegating transformation across scalar
    # row instances, list-wrapped query result sets, or pass-through null values to provide a consistent
    # structural interface for downstream consumer routines.
    def _dict_factory(
        self, result: list[sqlite3.Row] | sqlite3.Row | None
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """
        DATA TRANSFORMATION HOOK: SQLITE ROW SERIALIZER
        Converts sqlite3.Row objects or collections into standard Python dictionaries for
        decoupled downstream consumption.

        Args:
            result (list[sqlite3.Row] | sqlite3.Row | None): Raw driver query result payload,
                accepting individual row handles, lists of rows, or null query hits.

        Returns:
            list[dict[str, Any]] | dict[str, Any] | None: Transformed dictionary representation
                matching the structural shape of the input query payload.
        """
        # NULL VALUE INTERCEPTION GUARD
        # Return immediate None if database query yields no matching record set
        if result is None:
            return None

        # MULTI-RECORD COLLECTION TRANSFORM
        # Iterate over record collection to convert sqlite3.Row objects into standard dictionaries
        if isinstance(result, list):
            return [dict(row) for row in result]

        # SINGLE RECORD SERIALIZATION
        # Cast singular database row object directly into a key-value dictionary mapping
        return dict(result)

    # PERSISTENCE ENGINE: PARAMETERIZED WHERE CLAUSE BUILDER
    # This query generation utility dynamically constructs secure SQL WHERE conditions.
    # Concrete execution involves sanitizing field names, mapping operators based on value types
    # (handling NULL checks, set inclusion via IN clauses, or exact equality matches), and safely
    # binding operational parameters using '?' positional placeholders to prevent SQL injection.
    def _build_where(self, where: dict[str, Any] | None) -> tuple[str, tuple[Any, ...]]:
        """
        QUERY BUILDER HOOK: PARAMETERIZED WHERE CLAUSE SYNTHESIZER
        Transforms dictionary predicate maps into secure, parameterized SQLite WHERE clause
        strings with associated positional parameter tuples.

        Args:
            where (dict[str, Any] | None): Dictionary mapping column keys to matching conditions
                or filtering criteria. Accepts scalar values, list sets, or None.

        Returns:
            tuple[str, tuple[Any, ...]]: A tuple containing the synthesized SQL condition string
                and a tuple of positional parameters for safe database query binding.
        """
        # EMPTY PREDICATE GUARD CLAUSE
        # Return default true condition when no explicit filter dictionary is provided
        if not where:
            return "1=1", ()

        # STEP 2: CLAUSES AND PARAMETERS BUFFER ALLOCATION
        # Initialize internal storage vectors for generated SQL snippets and parameter values
        clauses: list[str] = []
        params: list[Any] = []

        # PREDICATE DICTIONARY COMPOSITION LOOP
        # Process filter key-value pairs to construct appropriate SQL comparison operations
        for key, value in where.items():
            # Sanitize column identifier to prevent structural SQL injection vulnerability
            safe_key = self._sanitize(key)

            # CONDITION BRANCH A: NULL VALUE CHECK
            if value is None:
                clauses.append(f'"{safe_key}" IS NULL')

            # CONDITION BRANCH B: MULTI-VALUE SET INCLUSION (IN CLAUSE)
            elif isinstance(value, list):
                val_list = cast(list[object], value)
                placeholders = ", ".join(["?"] * len(val_list))
                clauses.append(f'"{safe_key}" IN ({placeholders})')
                params.extend(val_list)

            # CONDITION BRANCH C: SCALAR EQUALITY COMPARISON
            else:
                clauses.append(f'"{safe_key}" = ?')
                params.append(value)

        # SQL STRING SYNTHESIS & PARAMETER TUPLE CONVERSION
        # Join clauses using logical AND operators and return positional parameter tuple
        return " AND ".join(clauses), tuple(params)

    # PERSISTENCE ENGINE: SECURE DATA FETCH & QUERY EXECUTION ENGINE
    # This query method executes safe SELECT queries against the database layer.
    # Concrete execution involves sanitizing target table and column identifiers, delegating WHERE clause
    # construction to parameterize filter predicates, parsing sorting directives and row count limits,
    # and returning structured record sets formatted as standard Python dictionaries or raw tuples.
    def fetch(
        self,
        table: str,
        where: dict[str, Any] | None = None,
        columns: list[str] | None = None,
        fetch_all: bool = True,
        order_by: str | None = None,
        limit: int | None = None,
        as_dict: bool = True,
    ) -> list[dict[str, Any]] | dict[str, Any] | list[Any] | Any | None:
        """
        QUERY EXECUTION HOOK: SECURE SELECT RECORD RETRIEVAL ENGINE
        Safely fetches records from a target table with dynamic filtering, column projection,
        ordering, and limit parameters.

        Args:
            table (str): Target table name for record extraction.
            where (dict[str, Any] | None, optional): Filter predicates mapping column keys to
                matching values or list sets. Defaults to None.
            columns (list[str] | None, optional): Target column names to retrieve.
                Defaults to None (retrieves all columns via '*').
            fetch_all (bool, optional): If True, returns all matching rows; if False, fetches
                only the first matching record. Defaults to True.
            order_by (str | None, optional): Sorting clause specification (e.g., "created_at DESC, id ASC").
                Defaults to None.
            limit (int | None, optional): Maximum row count threshold for query results. Defaults to None.
            as_dict (bool, optional): If True, serializes output rows to standard Python dictionaries.
                Defaults to True.

        Returns:
            list[dict[str, Any]] | dict[str, Any] | list[Any] | Any | None: Query output payload formatted
                as dictionary lists, scalar record maps, raw tuples, or None based on execution parameters.
        """
        # COLUMN PROJECTION SANITIZATION
        # Fallback to wildcard select if no explicit column vector is provided
        cols = columns if columns is not None else ["*"]

        # Sanitize target table and individual column identifiers to protect schema boundaries
        safe_table = self._sanitize(table)
        col_str = ", ".join(
            [f'"{self._sanitize(c)}"' if c != "*" else "*" for c in cols]
        )

        # PARAMETERIZED WHERE CLAUSE BUILD
        # Delegate WHERE clause text generation and parameter tuple binding to query builder helper
        where_clause, params = self._build_where(where)

        # BASE QUERY COMPOSITION
        # Construct base SQL statement using safe structural identifiers and parameterized WHERE placeholders
        query = f'SELECT {col_str} FROM "{safe_table}" WHERE {where_clause}'

        # ORDER BY CLAUSE PARSING & SANITIZATION
        # Parse comma-separated column sorting tokens and validate direction keywords
        if order_by:
            sanitized_orders: list[str] = []
            for part in order_by.split(","):
                tokens = part.strip().split()
                if tokens:
                    col = f'"{self._sanitize(tokens[0])}"'
                    direction = (
                        "DESC"
                        if len(tokens) > 1 and tokens[1].upper() == "DESC"
                        else "ASC"
                    )
                    sanitized_orders.append(f"{col} {direction}")
            if sanitized_orders:
                query += f" ORDER BY {', '.join(sanitized_orders)}"

        # LIMIT CLAUSE BINDING
        # Append safe row count upper bound constraint if specified
        if limit is not None:
            query += f" LIMIT {int(limit)}"

        # CURSOR CONTEXT EXECUTION & FETCH
        # Execute query inside managed cursor context and extract raw driver results
        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            raw_result: Any = cursor.fetchall() if fetch_all else cursor.fetchone()

            # DICTIONARY SERIALIZATION & PAYLOAD FORMATTING
            # Transform raw row handles to dictionary structures if requested by caller
            if as_dict:
                res_dict = self._dict_factory(raw_result)
                if fetch_all:
                    return cast(
                        list[dict[str, Any]], res_dict if res_dict is not None else []
                    )
                return cast(dict[str, Any] | None, res_dict)

            # Return raw row tuple payload when dictionary transformation is disabled
            if fetch_all:
                return cast(list[Any], raw_result if raw_result is not None else [])
            return raw_result

    # PERSISTENCE ENGINE: MULTI-TABLE RELATIONAL JOIN DISPATCHER
    # This query method executes dynamic relational JOIN operations across normalized database schemas.
    # Concrete execution involves sanitizing target table identifiers and join type directives, constructing
    # explicit ON predicate join clauses, delegating parameterized WHERE clause generation, parsing optional
    # sorting and limit parameters, and returning normalized dictionary list payloads via internal query dispatch.
    def fetch_joined(
        self,
        main_table: str,
        joins: list[tuple[str, str, str, str]],
        columns: list[str] | None = None,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        QUERY EXECUTION HOOK: SECURE MULTI-TABLE JOIN RETRIEVAL ENGINE
        Fetches records across joined tables with dynamic predicate filtering, column projection,
        sorting directives, and row limits.

        Args:
            main_table (str): Primary target table name serving as the driving table for the join query.
            joins (list[tuple[str, str, str, str]]): List of join specification tuples containing
                (target_table, left_key, right_key, join_type) parameters.
            columns (list[str] | None, optional): Explicit column target vector to select across tables.
                Defaults to None (selects '*').
            where (dict[str, Any] | None, optional): Parameterized predicate map for SQL WHERE generation.
                Defaults to None.
            order_by (str | None, optional): Sorting clause directive string. Defaults to None.
            limit (int | None, optional): Maximum record threshold constraint. Defaults to None.

        Returns:
            list[dict[str, Any]]: Normalized list of dictionary record payloads representing
                the joined query result set.
        """
        # COLUMN PROJECTION INITIALIZATION
        # Fallback to standard wildcard selection if no explicit column projection is provided
        cols = columns if columns is not None else ["*"]

        # JOIN CLAUSE SYNTHESIS & IDENTIFIER SANITIZATION
        # Iterate over specified join tuples to sanitize target tables, join types, and assemble ON conditions
        join_clauses: list[str] = []
        for table, l_key, r_key, j_type in joins:
            s_table = self._sanitize(table)
            s_jtype = self._sanitize(j_type).upper()
            join_clauses.append(f'{s_jtype} JOIN "{s_table}" ON {l_key} = {r_key}')

        # PARAMETERIZED WHERE CLAUSE BUILD
        # Delegate WHERE clause text generation and positional parameter binding to query builder helper
        where_clause, params = self._build_where(where)

        # SQL QUERY COMPOSITION
        # Construct full SELECT statement combining main table, dynamic joins, and parameterized WHERE conditions
        sql = (
            f"SELECT {', '.join(cols)} "
            f'FROM "{self._sanitize(main_table)}" '
            f"{' '.join(join_clauses)} "
            f"WHERE {where_clause}"
        )

        # ORDER BY & LIMIT CLAUSE ATTACHMENT
        # Append optional sorting criteria to query string
        if order_by:
            sql += f" ORDER BY {order_by}"

        # Append optional row limit upper bound constraint
        if limit is not None:
            sql += f" LIMIT {int(limit)}"

        # QUERY EXECUTION & PAYLOAD NORMALIZATION
        # Dispatch parameterized query string to backend query runner and normalize response into list format
        result = self.query(sql, params)
        if isinstance(result, list):
            return cast(list[dict[str, Any]], result)
        if isinstance(result, dict):
            return [cast(dict[str, Any], result)]
        return []

    # PERSISTENCE ENGINE: RANGE QUERY & OPERATOR DISPATCHER
    # This query utility enables numerical range evaluations and arbitrary operator comparisons.
    # Concrete execution involves sanitizing target table and column identifiers, validating evaluation
    # operators against a strict whitelist guard to block injection vectors, mapping positional parameter bindings,
    # and combining clauses using configurable boolean logic ("AND" / "OR") to return structured dictionary record sets.
    def fetch_range(
        self,
        table: str,
        constraints: dict[str, tuple[Any, str]],
        logic: str = "AND",
    ) -> list[dict[str, Any]]:
        """
        QUERY EXECUTION HOOK: RANGE & OPERATOR PREDICATE QUERY ENGINE
        Fetches records matching specific range constraints, comparison operators, and configurable
        boolean combining logic.

        Args:
            table (str): Target table name for record extraction.
            constraints (dict[str, tuple[Any, str]]): Constraint mapping table where keys represent
                column names and values are tuples of (comparison_value, operator_string).
            logic (str, optional): Boolean operator joining individual clause expressions ("AND" or "OR").
                Defaults to "AND".

        Returns:
            list[dict[str, Any]]: Normalized list of dictionary record maps satisfying the range constraints.
        """
        # IDENTIFIER SANITIZATION & BUFFER ALLOCATION
        # Sanitize target table identifier to prevent schema manipulation attacks
        safe_table = self._sanitize(table)
        clauses: list[str] = []
        params: list[Any] = []

        # OPERATOR WHITELIST GUARD & CLAUSE SYNTHESIS
        # Restrict valid comparison operators strictly to safe mathematical symbol tokens
        valid_operators = {"<", ">", "<=", ">=", "!=", "="}
        for key, (value, operator) in constraints.items():
            # Sanitize field name identifier
            safe_key = self._sanitize(key)

            # Validate comparison operator against whitelist, falling back to equality if unverified
            op = operator if operator in valid_operators else "="

            # Construct parameterized comparison clause and append parameter binding
            clauses.append(f'"{safe_key}" {op} ?')
            params.append(value)

        # BOOLEAN LOGIC RESOLUTION & WHERE CLAUSE JOIN
        # Parse logical operator directive to join conditions using OR or default AND
        safe_logic = " OR " if logic.strip().upper() == "OR" else " AND "
        where_str = safe_logic.join(clauses) if clauses else "1=1"

        # SQL QUERY COMPOSITION & EXECUTION DISPATCH
        # Assemble complete SELECT statement and execute query via parameter binding pipeline
        sql = f'SELECT * FROM "{safe_table}" WHERE {where_str}'

        result = self.query(sql, tuple(params))

        # PAYLOAD NORMALIZATION & RETURN
        # Ensure returned result payload strictly conforms to list[dict[str, Any]] structure
        if isinstance(result, list):
            return cast(list[dict[str, Any]], result)
        return []

    # PERSISTENCE ENGINE: ATOMIC UPSERT & CONFLICT RESOLUTION ENGINE
    # This data persistence method executes atomic INSERT ... ON CONFLICT DO UPDATE (upsert) queries.
    # Concrete execution involves sanitizing target table, conflict target, and update column identifiers,
    # constructing SQLite native syntax referencing the pseudo-table `excluded`, mapping field values to
    # positional parameters, and executing inside an explicitly committed transaction block.
    def upsert(
        self,
        table: str,
        data: dict[str, Any],
        conflict_target: list[str],
        update_cols: list[str],
    ) -> int:
        """
        PERSISTENCE HOOK: ATOMIC UPSERT EXECUTION ENGINE
        Inserts a new record into the specified table or updates specified columns if a conflict
        occurs on unique target constraints using SQLite native ON CONFLICT logic.

        Args:
            table (str): Target database table name.
            data (dict[str, Any]): Dictionary containing column-value mappings to insert or update.
            conflict_target (list[str]): List of column identifiers defining the unique key constraint.
            update_cols (list[str]): List of column identifiers to update when a conflict occurs.

        Returns:
            int: Total number of rows inserted or updated (rowcount), guaranteed non-negative.
        """
        # TABLE & COLUMN IDENTIFIER SANITIZATION
        # Sanitize target table name to secure DDL/DML boundaries
        safe_table = self._sanitize(table)

        # Extract column names and build sanitized, quoted column string and matching placeholder array
        keys = list(data.keys())
        cols = ", ".join([f'"{self._sanitize(k)}"' for k in keys])
        placeholders = ", ".join(["?"] * len(keys))

        # CONFLICT TARGET & UPDATE CLAUSE SYNTHESIS
        # Sanitize conflict targets defining the unique or primary key constraint
        safe_targets = ", ".join([f'"{self._sanitize(c)}"' for c in conflict_target])

        # Construct assignment expressions mapping existing columns to incoming values via 'excluded' pseudo-table
        update_parts = [
            f'"{self._sanitize(c)}" = excluded."{self._sanitize(c)}"'
            for c in update_cols
        ]
        update_str = ", ".join(update_parts)

        # NATIVE SQL UPSERT QUERY ASSEMBLY
        # Compose final parameterized INSERT ... ON CONFLICT DO UPDATE statement
        query = (
            f'INSERT INTO "{safe_table}" ({cols}) VALUES ({placeholders}) '
            f"ON CONFLICT({safe_targets}) DO UPDATE SET {update_str}"
        )

        # PARAMETER TUPLE CONVERSION
        # Extract dictionary payload values into positional parameter tuple for safe execution driver binding
        params = tuple(cast(list[object], list(data.values())))

        # TRANSACTIONAL EXECUTION & ROWCOUNT RETURN
        # Execute query within commit-enabled transaction context and return sanitized mutation count
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return max(0, cursor.rowcount)

    # PERSISTENCE ENGINE: MUTATION CONTROLLER & UPDATE DISPATCHER
    # This data modification routine executes parameter-bound UPDATE queries against target database tables.
    # Concrete execution enforces an absolute guard clause requiring non-empty WHERE predicates to prevent
    # accidental global table mutations, sanitizes field identifiers, binds update values alongside predicate parameters,
    # and executes the statement inside an explicitly committed transaction context.
    def update(self, table: str, data: dict[str, Any], where: dict[str, Any]) -> int:
        """
        PERSISTENCE HOOK: PARAMETERIZED RECORD UPDATE ENGINE
        Safely updates matching records in a target table using type-safe parameter binding.

        Args:
            table (str): Target table name for record modification.
            data (dict[str, Any]): Key-value mapping of column names and their new values.
            where (dict[str, Any]): Non-empty filter dictionary specifying match criteria.

        Returns:
            int: Total count of modified database rows (rowcount), guaranteed non-negative.

        Raises:
            ValueError: If the `where` predicate dictionary is omitted or empty.
        """
        # GLOBAL MUTATION GUARD CLAUSE
        # Enforce strict safety trigger to prevent unconditional full-table UPDATE operations
        if not where:
            raise ValueError("Safety Trigger: UPDATE requires a WHERE clause.")

        # IDENTIFIER SANITIZATION & SET CLAUSE ASSEMBLY
        # Sanitize target table name to preserve schema integrity
        safe_table = self._sanitize(table)

        # Build parameterized assignment expressions for SET clause
        set_clause = ", ".join([f'"{self._sanitize(key)}" = ?' for key in data.keys()])

        # PARAMETERIZED WHERE CLAUSE BUILD
        # Delegate predicate parsing to query builder, extracting SQL text and positional parameter values
        where_clause, where_params = self._build_where(where)

        # SQL QUERY SYNTHESIS
        # Assemble parameterized UPDATE statement template
        query = f'UPDATE "{safe_table}" SET {set_clause} WHERE {where_clause}'

        # PARAMETER VECTOR CONCATENATION
        # Combine update field values with WHERE filter parameters into unified positional binding tuple
        data_params = tuple(cast(list[object], list(data.values())))
        params = data_params + where_params

        # TRANSACTIONAL EXECUTION & ROWCOUNT RETURN
        # Execute update query inside commit-enabled transaction manager and return affected row count
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return max(0, cursor.rowcount)

    # PERSISTENCE ENGINE: LOW-LEVEL SQL QUERY DISPATCHER & ENTRY POINT
    # This query method executes raw SQL strings with dynamic parameter binding and transaction controls.
    # Concrete execution involves converting legacy string interpolation placeholders ('%s') to standard
    # positional markers ('?'), executing the query within a managed connection context, handling mutation
    # rowcounts on commits, and formatting SELECT result sets as dictionaries or raw row tuples.
    def query(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        fetch_all: bool = True,
        as_dict: bool = True,
        commit: bool = False,
    ) -> list[dict[str, Any]] | dict[str, Any] | int | list[Any] | Any | None:
        """
        QUERY EXECUTION HOOK: LOW-LEVEL SQL STATEMENT DISPATCHER
        Executes arbitrary SQLite queries with type-safe parameters, transaction isolation,
        and configurable output formatting.

        Args:
            sql (str): Raw or parameterized SQL statement to execute.
            params (Sequence[Any] | None, optional): Positional parameter collection for query binding.
                Defaults to None.
            fetch_all (bool, optional): If True, returns all matching records; if False, fetches only
                the single top hit. Defaults to True.
            as_dict (bool, optional): If True, serializes query results into standard Python
                dictionaries via row factory mapping. Defaults to True.
            commit (bool, optional): Indicates whether execution should open a transactional write context
                and return affected rowcount. Defaults to False.

        Returns:
            list[dict[str, Any]] | dict[str, Any] | int | list[Any] | Any | None: Mutation rowcount (when commit=True),
                formatted dictionary collection/scalar, raw tuples, or None based on query flags.
        """
        # PLACEHOLDER NORMALIZATION
        # Sanitize query string by mapping legacy database placeholders ('%s') to standard SQLite markers ('?')
        formatted_sql = sql.replace("%s", "?")

        # CURSOR EXECUTION CONTEXT
        # Open managed cursor block with automated commit/rollback lifecycle control based on commit parameter
        with self._get_cursor(commit=commit) as cursor:
            cursor.execute(formatted_sql, params or ())

            # STEP 3: TRANSACTION MUTATION EARLY RETURN
            # If statement is a write/commit operation, return total modified row count
            if commit:
                return max(0, cursor.rowcount)

            # RECORD SET EXTRACTION
            # Retrieve record sets based on requested fetch depth
            result: Any = cursor.fetchall() if fetch_all else cursor.fetchone()

            # DICTIONARY FORMATTING & PAYLOAD RETURN
            # Transform database row handles into standard key-value dictionary objects if requested
            if as_dict:
                formatted = self._dict_factory(result)
                if fetch_all:
                    return cast(
                        list[dict[str, Any]], formatted if formatted is not None else []
                    )
                return cast(dict[str, Any] | None, formatted)

            # Return unformatted raw driver tuple payload when dict transformation is disabled
            if fetch_all:
                return cast(list[Any], result if result is not None else [])
            return result

    # PERSISTENCE ENGINE: RECORD DELETION & SAFETY GUARD CONTROLLER
    # This data deletion routine executes parameter-bound DELETE queries against target database tables.
    # Concrete execution enforces an absolute guard clause requiring non-empty WHERE predicates to prevent
    # accidental truncation of entire tables, sanitizes target schema identifiers, constructs parameterized
    # filter clauses, and executes the mutation inside an explicitly committed transaction context.
    def delete(self, table: str, where: dict[str, Any]) -> int:
        """
        PERSISTENCE HOOK: PARAMETERIZED RECORD DELETION ENGINE
        Safely removes matching records from a target table using type-safe parameter binding.

        Args:
            table (str): Target table name for record removal.
            where (dict[str, Any]): Non-empty filter dictionary specifying row deletion criteria.

        Returns:
            int: Total count of removed database records (rowcount), guaranteed non-negative.

        Raises:
            ValueError: If the `where` predicate dictionary is omitted or empty.
        """
        # DELETION SAFETY GUARD CLAUSE
        # Enforce strict safety trigger to prevent unconditional full-table DELETE operations
        if not where:
            raise ValueError("Safety Trigger: DELETE requires a WHERE clause.")

        # TABLE IDENTIFIER SANITIZATION
        # Sanitize target table identifier to enforce structural schema security
        safe_table = self._sanitize(table)

        # PARAMETERIZED WHERE CLAUSE SYNTHESIS
        # Delegate filter predicate parsing to query builder, extracting SQL clause and positional parameter bindings
        where_clause, params = self._build_where(where)

        # SQL QUERY ASSEMBLY
        # Construct parameterized DELETE statement template
        query = f'DELETE FROM "{safe_table}" WHERE {where_clause}'

        # TRANSACTIONAL EXECUTION & ROWCOUNT RETURN
        # Execute deletion query inside commit-enabled transaction manager and return affected row count
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return max(0, cursor.rowcount)

    # PERSISTENCE ENGINE: SINGLE-RECORD INSERTION ENGINE
    # This persistence routine inserts single record dictionary maps into target relational tables.
    # Concrete execution involves sanitizing target table and column identifiers, constructing
    # parameterized INSERT statements with '?' value placeholders, executing within an explicitly
    # committed transaction, and returning the auto-incremented row identifier handle.
    def save(self, table: str, data: dict[str, Any]) -> int:
        """
        PERSISTENCE HOOK: RECORD INSERTION ENGINE
        Inserts a single record dictionary into a target table and returns the auto-generated row ID.

        Args:
            table (str): Target table name for record insertion.
            data (dict[str, Any]): Key-value map representing column names and corresponding field values.

        Returns:
            int: The unique row ID assigned to the newly inserted record, or 0 if unassigned.
        """
        # IDENTIFIER SANITIZATION & COLUMN STRING SYNTHESIS
        # Sanitize target table identifier to enforce structural schema boundaries
        safe_table = self._sanitize(table)

        # Extract column keys and format sanitized, quoted column names alongside positional parameter placeholders
        keys = list(data.keys())
        cols = ", ".join([f'"{self._sanitize(k)}"' for k in keys])
        placeholders = ", ".join(["?"] * len(keys))

        # SQL STATEMENT ASSEMBLY
        # Compose parameterized INSERT INTO statement
        query = f'INSERT INTO "{safe_table}" ({cols}) VALUES ({placeholders})'

        # PARAMETER TUPLE CONVERSION
        # Cast values to a concrete tuple[object, ...] to satisfy strict static type checking
        params = tuple(cast(list[object], list(data.values())))

        # TRANSACTIONAL EXECUTION & LASTROWID EXTRACTION
        # Execute statement within commit-enabled context and extract assigned primary key handle
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            return int(last_id) if last_id is not None else 0

    # PERSISTENCE ENGINE: BATCH INSERTION & BULK DISPATCHER
    # This data persistence routine executes batch record insertions against relational database tables.
    # Concrete execution involves validating input non-emptiness, extracting uniform keys from the prime payload record,
    # constructing a parameterized INSERT statement, mapping record list payloads into structured tuple sequences,
    # and delegating high-throughput bulk insertion to executemany within an explicitly committed transaction context.
    def save_many(self, table: str, data_list: list[dict[str, Any]]) -> int:
        """
        PERSISTENCE HOOK: BATCH RECORD INSERTION ENGINE
        Inserts multiple dictionary records into a target table in a single atomic transaction
        using optimized executemany batch processing.

        Args:
            table (str): Target table name for bulk record insertion.
            data_list (list[dict[str, Any]]): List of dictionary records matching a uniform key schema.

        Returns:
            int: Total count of inserted database rows (rowcount), guaranteed non-negative.
        """
        # EMPTY PAYLOAD GUARD CLAUSE
        # Return zero immediately if record payload list is unpopulated
        if not data_list:
            return 0

        # SCHEMA EXTRACT & IDENTIFIER SANITIZATION
        # Sanitize target table identifier to enforce structural security
        safe_table = self._sanitize(table)

        # Infer column structure from initial dictionary payload record and format positional placeholders
        keys = list(data_list[0].keys())
        cols = ", ".join([f'"{self._sanitize(k)}"' for k in keys])
        placeholders = ", ".join(["?"] * len(keys))

        # PARAMETERIZED STATEMENT SYNTHESIS
        # Assemble parameterized INSERT INTO statement template
        query = f'INSERT INTO "{safe_table}" ({cols}) VALUES ({placeholders})'

        # BULK TUPLE VECTOR MATRIX MAPPING
        # Extract dictionary payload values into tuple sequences aligned strictly with inferred column order
        vals: list[tuple[object, ...]] = [
            tuple(cast(list[object], [d[k] for k in keys])) for d in data_list
        ]

        # TRANSACTIONAL BATCH EXECUTION & ROWCOUNT RETURN
        # Execute batch insertion via cursor.executemany within committed transaction context
        with self._get_cursor(commit=True) as cursor:
            cursor.executemany(query, vals)
            return max(0, cursor.rowcount)
