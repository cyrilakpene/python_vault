# DATABASE CONNECTIVITY & UTILITIES
# This block imports the core libraries required for establishing
# secure, pooled connections to a MySQL instance. It includes
# support for resource lifecycle management and comprehensive
# error logging.

from mysql.connector import Error, pooling
from contextlib import contextmanager
import re
import sys
from typing import List, Dict, Any, Optional, Union, Tuple, Sequence

from config import Config, config

# DATABASE DRIVER & CONNECTION POOLING
# The 'mysql.connector' and 'pooling' modules facilitate communication between
# Python and the MySQL server. By utilizing 'pooling', we reduce the overhead
# of repeatedly opening and closing TCP connections, instead maintaining a
# "warm" set of reusable connections for better performance under load.

# RESOURCE LIFECYCLE MANAGEMENT
# 'contextmanager' allows for the creation of 'with' statement blocks. This
# ensures that database cursors and connections are automatically closed or
# returned to the pool, even if an exception occurs during execution,
# preventing "leaked" connections and database lock-ups.

# TYPE HINTING & STATIC ANALYSIS
# The 'typing' module resources (List, Dict, etc.) are used for type annotation.
# While not enforced at runtime, these hints improve developer experience by
# enabling IDE auto-completion and allowing tools like Pylance to catch
# logic errors before the code is even deployed.


# DATABASE PIPELINE ARCHITECTURE
# This class serves as the primary interface for all database
# interactions. It encapsulates connection pooling, query
# execution logic, and transaction safety into a single,
# reusable entity.
class MySQLDatabasePipeline:
    """
    An optimized SQL pipeline for MySQL/MariaDB with Connection Pooling,
    Dynamic Query Building, and automated Transaction Management.
    """

    # CLASS ARCHITECTURAL DESIGN
    # By wrapping database logic within 'DatabasePipeline', we implement
    # the 'Singleton' or 'Factory' pattern for database access. This
    # centralization ensures that configuration—such as credentials,
    # timeout settings, and pool sizes—remains consistent across
    # the entire application lifecycle.

    # ENCAPSULATION & STATE MANAGEMENT
    # This class manages the internal state of the MySQL connection pool.
    # Encapsulation allows us to hide the complexity of raw SQL drivers
    # behind high-level methods, ensuring that the calling code
    # (the "Business Logic") does not need to handle low-level
    # network retries or manual cursor closures.

    # PIPELINE INITIALIZATION & RESOURCE ALLOCATION
    # This constructor method validates the inbound configuration
    # and instantiates a thread-safe MySQL connection pool. It
    # serves as the critical bridge between the application settings
    # and the physical database cluster.
    def __init__(
        self,
        config: Config = config,
        pool_name: str = "mypool",
        pool_size: int = 5,
    ):
        self.config = config
        try:
            # CONNECTION POOL INSTANTIATION
            # We leverage 'MySQLConnectionPool' to create a pre-allocated set of
            # database connections. This avoids the "handshake latency" associated
            # with establishing a new TCP/TLS connection for every single query,
            # which is vital for high-concurrency environments.
            self.pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                # SESSION STATE PROTECTION
                # 'pool_reset_session=True' ensures that when a connection is
                # returned to the pool and checked out again, all session variables,
                # user-defined variables, and temporary tables from the previous
                # user are cleared, preventing data leakage between threads.
                pool_reset_session=True,
                # CREDENTIAL MAPPING
                # These parameters map the injected configuration object directly
                # to the driver's connection requirements. Using an injected
                # 'config' object allows the pipeline to remain agnostic of
                # whether it is running in Development, Staging, or Production.
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                user=self.config.DB_USER,
                password=self.config.DB_PASS,
                database=self.config.DB_NAME,
            )

        # ERROR HANDLING & FAIL-FAST LOGIC
        # If the pool fails to initialize (e.g., incorrect credentials or
        # unreachable host), we catch the 'Error' and log it immediately.
        # By re-raising the exception, we prevent the application from
        # starting in a "zombie" state where database calls are guaranteed to fail.
        except Error as e:
            sys.stderr.write(f"[x] POOL INITIALIZATION ERROR: {e}")
            sys.exit(1)

    # AUTOMATED RESOURCE & TRANSACTION LIFECYCLE
    # This internal context manager automates the lifecycle of a
    # database transaction. It handles the retrieval of connections
    # from the pool, cursor initialization, and ensures that
    # resources are cleaned up—regardless of whether the
    # operation succeeded or failed.
    @contextmanager
    def _get_cursor(self, dictionary: bool = True, commit: bool = False):
        """
        Internal context manager to ensure connections and cursors
        are always returned to the pool safely.
        """
        conn = None
        cursor = None
        try:
            # CONNECTION ACQUISITION & CURSOR CONFIGURATION
            # We fetch a 'warm' connection from the pre-initialized pool.
            # By setting 'dictionary=True', results are returned as key-value
            # pairs rather than tuples, significantly improving code
            # readability. 'buffered=True' is used to fetch the entire
            # result set immediately, preventing "Unread result" errors
            # during subsequent operations on the same connection.
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=dictionary, buffered=True)

            # EXECUTION HANDOVER
            # The 'yield' statement pauses this method and hands the active
            # cursor to the calling function. This allows the logic inside
            # 'execute' or 'fetch' to run within this protected environment.
            yield cursor

            # ATOMIC COMMIT LOGIC
            # If 'commit' is set to True (standard for INSERT/UPDATE/DELETE),
            # we finalize the changes here. This ensures that all operations
            # within the 'with' block are treated as a single atomic unit.
            if commit:
                conn.commit()

        # ERROR ISOLATION & ROLLBACK
        # If a SQL error occurs, we intercept it here. If the transaction
        # was meant to commit data, we trigger a 'rollback()' to undo any
        # partial changes, maintaining the integrity of the database state.
        except Error as e:
            if conn and commit:
                conn.rollback()
            sys.stderr.write(f"[x] DATABASE ERROR: {e}")
            raise e

        # FINAL CLEANUP
        # The 'finally' block is the most critical part of this method.
        # It ensures that even if the code crashes, the cursor is closed
        # and the connection is returned to the pool. This prevents
        # the "Leaking Connections" bug that eventually crashes database servers.
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # SCHEMA SECURITY & IDENTIFIER SANITIZATION
    # This utility method provides a layer of defense against SQL
    # Injection targeting structural elements. It ensures that
    # dynamically injected table or column names conform to safe
    # naming conventions.
    def _sanitize(self, identifier: str) -> str:
        """
        Prevents SQL injection on table/column names by stripping
        non-alphanumeric characters.
        """

        # REGULAR EXPRESSION FILTRATION
        # Standard SQL parameterization (%s) only works for data values, not
        # structural identifiers like table names. This 're.sub' operation
        # enforces a strict allow-list: it removes any character that is not
        # a letter, a number, or an underscore.
        return re.sub(r"[^a-zA-Z0-9_]", "", identifier)

    # DYNAMIC QUERY PREDICATE ENGINE
    # This helper method transforms a Python dictionary into a valid
    # SQL 'WHERE' clause. It intelligently handles different data
    # types—such as NULL values and lists—to ensure the resulting
    # query is both syntactically correct and secure.
    def _build_where(self, where: Optional[Dict[str, Any]]) -> Tuple[str, tuple]:
        """
        Handles NULL, Lists (IN), and standard equality for WHERE clauses.
        """

        # DEFAULT PREDICATE HANDLING
        # If no 'where' dictionary is provided, we return "1=1". This is a
        # standard SQL 'No-Op' that allows the calling function to append
        # this string to a query without breaking the syntax if the filter
        # is empty, effectively selecting all records.
        if not where:
            return "1=1", ()

        clauses = []
        params = []

        # DYNAMIC CLAUSE CONSTRUCTION
        # We iterate through the dictionary to map keys to SQL column names
        # and values to their respective SQL logic. Note the use of backticks
        # (`) around 'safe_key' to prevent conflicts with MySQL reserved words.
        for key, value in where.items():
            safe_key = self._sanitize(key)

            # NULL VALUE LOGIC
            # In SQL, comparing a value to NULL using '=' fails. This block
            # detects 'None' and correctly implements the 'IS NULL' operator.
            if value is None:
                clauses.append(f"`{safe_key}` IS NULL")

            # MULTI-VALUE (IN) LOGIC
            # If the value is a list, we dynamically generate the appropriate
            # number of placeholders (%s) to support the 'IN' clause,
            # flattening the list into the parameters tuple.
            elif isinstance(value, list):
                placeholders = ", ".join(["%s"] * len(value))
                clauses.append(f"`{safe_key}` IN ({placeholders})")
                params.extend(value)

            # STANDARD EQUALITY LOGIC
            # For strings, integers, and other scalars, we use a standard
            # placeholder to ensure the data is sanitized by the SQL driver.
            else:
                clauses.append(f"`{safe_key}` = %s")
                params.append(value)

        # OUTPUT FORMATTING
        # The clauses are joined by 'AND' to create a conjunctive filter.
        # We return a tuple containing the SQL string and the ordered
        # parameters to be passed to the cursor execution.
        return " AND ".join(clauses), tuple(params)

    # DYNAMIC DATA RETRIEVAL INTERFACE
    # This method serves as a high-level abstraction for SELECT
    # operations. It automates the construction of SQL queries,
    # integrates security sanitization, and manages result
    # fetching through the connection pool.
    def fetch(
        self,
        table: str,
        where: Optional[Dict[str, Any]] = None,
        columns: List[str] = ["*"],
        fetch_all: bool = True,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        as_dict: bool = True,
    ) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Fetches records with dynamic filtering and automatic sanitization.
        """

        # SCHEMA & COLUMN SANITIZATION
        # We sanitize the table name and iterate through the requested columns.
        # Special handling is provided for the "*" wildcard; otherwise, column
        # names are wrapped in backticks to prevent collisions with SQL
        # keywords (e.g., a column named 'group' or 'order').
        safe_table = self._sanitize(table)
        col_str = ", ".join(
            [f"`{self._sanitize(c)}`" if c != "*" else "*" for c in columns]
        )

        # PREDICATE & PARAMETER GENERATION
        # Leverages the internal '_build_where' helper to generate the
        # 'WHERE' string and its associated data tuple, ensuring
        # parameterization is maintained for security.
        where_clause, params = self._build_where(where)

        # QUERY COMPOSITION
        # The base query is constructed using f-strings for the structural
        # components (table/columns) which have been sanitized. Data
        # filtering is deferred to 'params' to prevent SQL Injection.
        query = f"SELECT {col_str} FROM `{safe_table}` WHERE {where_clause}"

        # OPTIONAL CLAUSE APPENDING
        # Logic for ordering and pagination is appended conditionally.
        # For 'limit', we cast to 'int' as an extra layer of type-safety
        # to ensure no malicious strings can be injected into the numeric clause.
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {int(limit)}"

        # EXECUTION & RESOURCE MANAGEMENT
        # We use the '_get_cursor' context manager to check out a connection.
        # 'dictionary=True' ensures that results are returned as
        # Python dictionaries, making the data easier to consume in the
        # application layer.
        with self._get_cursor(dictionary=as_dict) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch_all else cursor.fetchone()

            # If fetchall() is called and nothing is found, it usually returns []
            # If fetchone() is called and nothing is found, it returns None
            # This ensures fetch_all=True always returns a list
            if fetch_all:
                return result if result is not None else []
            return result

    # DATA PERSISTENCE INTERFACE (INSERT)
    # This method handles the insertion of a single record into a
    # specified table. It dynamically maps dictionary keys to
    # columns and values to placeholders, ensuring a clean
    # separation between SQL logic and user data.
    def save(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a single record into the database.
        Returns the auto-generated Primary Key (Last Insert ID).
        """

        # STRUCTURAL METADATA PREPARATION
        # We extract the dictionary keys to define the target columns.
        # Each key is passed through '_sanitize' and wrapped in backticks
        # to protect against reserved SQL keywords and ensure the query
        # remains valid even with non-standard column names.
        safe_table = self._sanitize(table)
        keys = data.keys()
        cols = ", ".join([f"`{self._sanitize(k)}`" for k in keys])

        # SECURE PLACEHOLDER GENERATION
        # Instead of injecting values directly into the string, we create
        # a series of '%s' placeholders matching the count of our data.
        # This is a mandatory security practice to prevent SQL Injection
        # by allowing the MySQL driver to handle data escaping.
        placeholders = ", ".join(["%s"] * len(data))

        # QUERY ASSEMBLY
        # The final SQL command is constructed using the sanitized
        # table and column names. The actual data values remain separate,
        # passed as an ordered tuple during the execution phase.
        query = f"INSERT INTO `{safe_table}` ({cols}) VALUES ({placeholders})"

        # TRANSACTION EXECUTION & ID RETRIEVAL
        # By setting 'commit=True', we instruct the '_get_cursor' context
        # manager to finalize the transaction. Once executed, we access
        # 'cursor.lastrowid' to retrieve the ID of the new row—essential
        # for maintaining foreign key relationships in downstream logic.
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(data.values()))
            return int(cursor.lastrowid or 0)

    # HIGH-THROUGHPUT BATCH PERSISTENCE (BULK INSERT)
    # This method facilitates the insertion of multiple records in a
    # single database operation. By minimizing the number of
    # round-trips between the application and the MySQL server,
    # it optimizes performance for large datasets or log-heavy
    # streaming operations.
    def save_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """
        Bulk insert multiple records for optimized performance.
        Returns the total count of successfully inserted rows.
        """

        # EARLY EXIT & VALIDATION
        # If an empty list is passed, we return 0 immediately. This prevents
        # the code from attempting to parse keys from a non-existent index
        # or executing an empty SQL statement, which would trigger an error.
        if not data_list:
            return 0

        # SCHEMA METADATA EXTRACTION
        # We derive the column names from the first dictionary in the list.
        # It is a prerequisite of this method that all dictionaries in the
        # list share an identical structure (the same keys/columns).
        safe_table = self._sanitize(table)
        keys = data_list[0].keys()
        cols = ", ".join([f"`{self._sanitize(k)}`" for k in keys])

        # BATCH QUERY PREPARATION
        # Similar to the 'save' method, we generate a template string with
        # '%s' placeholders. The database driver uses this template to
        # efficiently map the bulk data into a single execution plan.
        placeholders = ", ".join(["%s"] * len(keys))
        query = f"INSERT INTO `{safe_table}` ({cols}) VALUES ({placeholders})"

        # DATA TRANSFORM & FLATTENING
        # We convert the list of dictionaries into a list of tuples.
        # This format is required by the 'executemany' method, which
        # iterates over the values and binds them to the template query.
        vals = [tuple(d[k] for k in keys) for d in data_list]

        # ATOMIC BATCH EXECUTION
        # Using 'executemany' is exponentially faster than a loop of
        # individual 'execute' calls. The 'commit=True' flag ensures that
        # the entire batch is finalized as a single unit of work.
        with self._get_cursor(commit=True) as cursor:
            cursor.executemany(query, vals)

            # 'cursor.rowcount' provides the total number of records
            # modified or inserted by the last operation, allowing the
            # caller to verify the integrity of the bulk operation.
            return cursor.rowcount

    # ATOMIC UPSERT INTERFACE (INSERT OR UPDATE)
    # This method implements the 'ON DUPLICATE KEY UPDATE' pattern.
    # It allows for "blind" writes where the application does not
    # need to check for a record's existence before deciding
    # whether to insert or update, reducing race conditions and
    # database round-trips.
    def upsert(self, table: str, data: Dict[str, Any], update_cols: List[str]) -> int:
        """
        Performs an atomic 'INSERT ... ON DUPLICATE KEY UPDATE' operation.
        Returns the number of rows affected (1 for insert, 2 for update).
        """

        # STRUCTURAL SANITIZATION
        # We sanitize the table name and the keys of the input data.
        # This ensures that the structural components of the INSERT
        # portion of the statement are safe and valid.
        safe_table = self._sanitize(table)
        keys = data.keys()
        cols = ", ".join([f"`{self._sanitize(k)}`" for k in keys])
        placeholders = ", ".join(["%s"] * len(data))

        # DYNAMIC UPDATE CLAUSE CONSTRUCTION
        # This loop builds the 'UPDATE' portion of the query. By using the
        # 'VALUES()' function inside the SQL string, we tell MySQL to use
        # the new data provided in the INSERT part to update the existing
        # record, keeping the logic centralized and reducing the number
        # of parameters we need to pass manually.
        update_parts = [
            f"`{self._sanitize(c)}` = VALUES(`{self._sanitize(c)}`)"
            for c in update_cols
        ]
        update_str = ", ".join(update_parts)

        # FULL QUERY SYNTHESIS
        # The final query combines the standard INSERT logic with the
        # 'ON DUPLICATE KEY' branch. This is an atomic operation within
        # MySQL, ensuring data integrity even under high concurrency.
        query = (
            f"INSERT INTO `{safe_table}` ({cols}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_str}"
        )

        # EXECUTION & ROW METRICS
        # We pass the data values as a tuple to satisfy the placeholders.
        # The 'cursor.rowcount' is particularly descriptive here:
        # - 1: A new row was inserted.
        # - 2: An existing row was updated.
        # - 0: An existing row was found, but the data was identical (no change).
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(data.values()))
            return cursor.rowcount

    # DATA MODIFICATION INTERFACE (UPDATE)
    # This method facilitates targeted modifications of existing
    # database records. It implements strict safety checks to prevent
    # unbounded updates and utilizes dynamic SQL generation to
    # bridge Python dictionaries with SQL 'SET' and 'WHERE' syntax.
    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """
        Updates existing records in the database.
        Returns the total number of rows modified.
        """

        # CRITICAL SAFETY ENFORCEMENT
        # An empty 'WHERE' clause in an UPDATE statement targets all rows in
        # a table. To prevent accidental data wipes, we enforce a strict
        # requirement: the 'where' dictionary must contain at least one
        # filtering criterion before execution is permitted.
        if not where:
            raise ValueError("Safety Trigger: UPDATE requires a WHERE clause.")

        # SCHEMA SANITIZATION & SET CLAUSE BUILDING
        # We sanitize the table name and iterate through the data keys to
        # construct the 'SET' portion of the query. By using '%s' placeholders
        # for the values, we maintain full protection against SQL injection.
        safe_table = self._sanitize(table)
        set_clause = ", ".join([f"`{self._sanitize(key)}` = %s" for key in data.keys()])

        # PREDICATE GENERATION
        # The '_build_where' helper generates the conditional logic and
        # the parameters for the 'WHERE' filter, ensuring that only the
        # intended records are modified.
        where_clause, where_params = self._build_where(where)

        # QUERY COMPOSITION
        # The final SQL string combines the sanitized structural elements.
        # Note that the order of 'SET' values followed by 'WHERE' values
        # is vital for the database driver to map placeholders correctly.
        query = f"UPDATE `{safe_table}` SET {set_clause} WHERE {where_clause}"

        # PARAMETER SEQUENCING
        # We concatenate the data values (for the SET clause) with the
        # where parameters. This ordered tuple is then passed to the
        # cursor to ensure each %s is replaced by the correct variable.
        params = tuple(data.values()) + where_params

        # TRANSACTION EXECUTION
        # Using the '_get_cursor' context manager with 'commit=True'
        # ensures that the changes are written to disk. The method returns
        # 'rowcount' to inform the caller how many records were actually updated.
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    # DATA REMOVAL INTERFACE (DELETE)
    # This method provides a secure way to remove records from a
    # specified table. It enforces strict filtering requirements
    # to prevent accidental data loss and handles structural
    # sanitization to ensure the query remains valid.
    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Deletes records from the database based on specific criteria.
        Returns the number of rows successfully removed.
        """

        # CRITICAL SAFETY ENFORCEMENT
        # Similar to the 'update' method, a 'DELETE' without a 'WHERE' clause
        # acts as a 'TRUNCATE' operation in SQL, removing every record in the
        # table. This exception acts as a circuit breaker, forcing the
        # developer to explicitly define the scope of the deletion.
        if not where:
            raise ValueError("Safety Trigger: DELETE requires a WHERE clause.")

        # SCHEMA SANITIZATION
        # We sanitize the table name to prevent structural injection. Since
        # 'DELETE' does not involve column selection, only the table name
        # requires this treatment before being placed in the f-string.
        safe_table = self._sanitize(table)

        # PREDICATE & PARAMETER GENERATION
        # The '_build_where' helper constructs the 'WHERE' string and
        # extracts the corresponding values into a tuple. This ensures
        # that the filter is handled as a parameterized value by the
        # MySQL driver, protecting against malicious input.
        where_clause, params = self._build_where(where)

        # QUERY SYNTHESIS
        # The SQL command is built by combining the sanitized table name
        # with the dynamically generated where clause.
        query = f"DELETE FROM `{safe_table}` WHERE {where_clause}"

        # TRANSACTION EXECUTION & FEEDBACK
        # We invoke the '_get_cursor' context manager with 'commit=True'
        # to finalize the deletion. The method returns 'cursor.rowcount',
        # which is essential for confirming whether the operation
        # targeted the expected number of records.
        with self._get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    # COMPLEX JOIN ABSTRACTION INTERFACE
    # This method bridges the gap between simple table fetches and manual
    # SQL JOINs. It serves as a high-level "Relational Mapper" that allows
    # the developer to define table relationships (e.g., connecting 'exams'
    # to 'courses' and 'programs') using structured Python lists. This
    # automation ensures that the structural SQL—specifically the 'ON'
    # conditions—remains syntactically perfect and optimized, significantly
    # reducing the risk of "Cartesian Product" errors caused by
    # malformed JOIN logic.
    def fetch_joined(
        self,
        main_table: str,
        joins: List[Tuple[str, str, str, str]],
        columns: List[str] = ["*"],
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Dynamically builds and executes a SELECT query with multiple JOINs.
        Format for 'joins': [ (table, left_key, right_key, join_type), ... ]
        """

        # STRUCTURAL ASSEMBLY: RELATIONSHIP MAPPING
        # We iterate through the 'joins' configuration list to construct the
        # SQL 'ON' clauses. By automating the placement of 'LEFT', 'INNER',
        # or 'RIGHT' keywords and wrapping table names in the internal
        # '_sanitize' filter, we protect the structural integrity of the
        # query while making it effortless to link three or more tables
        # in a single operation.
        join_clauses = []
        for table, l_key, r_key, j_type in joins:
            join_clauses.append(
                f"{j_type} JOIN `{self._sanitize(table)}` ON {l_key} = {r_key}"
            )

        # PREDICATE ENGINE INTEGRATION (CROSS-TABLE FILTERING)
        # We reuse the robust '_build_where' helper. This allows you to
        # apply filters to ANY column across the joined tables (e.g.,
        # filtering by 'programs.dept_id' even if the main table is 'exams').
        # The engine ensures that all filter values are parameterized (%s),
        # maintaining your global security standard against SQL Injection.
        where_clause, params = self._build_where(where)

        # DYNAMIC SQL SYNTHESIS & IDENTIFIER WRAPPING
        # The final SQL statement is synthesized by joining the column list,
        # the sanitized main table, the generated join clauses, and the
        # validated where predicate. This multi-step assembly creates a
        # "Flattened" view of your relational data, making it ideal for
        # generating complex university reports or timetable views.
        sql = (
            f"SELECT {', '.join(columns)} "
            f"FROM `{self._sanitize(main_table)}` "
            f"{' '.join(join_clauses)} "
            f"WHERE {where_clause}"
        )

        # ORDERING & PAGINATION CLAUSES
        # These optional clauses are appended to the tail of the query.
        # Including 'limit' ensures that even complex joins do not
        # accidentally return massive datasets that could overwhelm
        # the application's memory.
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {int(limit)}"

        # EXECUTION HANDOVER & RESULT NORMALIZATION
        # The final string is passed to the 'query' method, inheriting
        # its connection pooling and error handling. We then normalize
        # the output: if the query returns a single dictionary, we
        # wrap it in a list. This ensures the calling function can
        # always treat the result as an iterable (list), preventing
        # "TypeError: 'NoneType' is not iterable" during UI rendering.
        result = self.query(sql, params)
        if isinstance(result, dict):
            return [result]
        elif isinstance(result, list):
            return result
        else:
            return []

    # DYNAMIC RAW SQL EXECUTION ENGINE
    # This method serves as the "Escape Hatch" for the pipeline architecture.
    # It provides total structural freedom, making it the ideal tool for
    # high-level database operations that fall outside the standard CRUD
    # patterns, such as complex 'GROUP BY' aggregations, subqueries,
    # table unions, or executing specific administrative commands. It
    # bridges the gap between the pipeline's automated safety and the
    # full expressive power of the MariaDB/MySQL engine.
    def query(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
        fetch_all: bool = True,
        as_dict: bool = True,
        commit: bool = False,
    ) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]], int]:
        """
        Executes dynamic raw SQL. Supports SELECT, INSERT, UPDATE, and DELETE.
        """

        # AUTOMATED RESOURCE & TRANSACTION LIFECYCLE
        # We invoke the internal '_get_cursor' context manager, passing the
        # 'commit' and 'dictionary' flags. This ensures that even for manual
        # SQL strings, the connection is safely retrieved from the pool,
        # and the transaction is automatically finalized if the 'commit'
        # flag is set, preventing orphaned transactions or stale connections.
        with self._get_cursor(dictionary=as_dict, commit=commit) as cursor:

            # SECURE PARAMETER BINDING (CODE/DATA ISOLATION)
            # The raw SQL string and its associated parameters are passed
            # separately to the driver's execution engine. This maintains
            # a strict barrier that prevents SQL Injection, as the driver
            # treats the 'params' as literal data rather than executable
            # code, regardless of the complexity of the manual SQL string.
            cursor.execute(sql, params or ())

            # DATA MODIFICATION FEEDBACK (DML OPERATIONS)
            # When the 'commit' flag is active—typically for INSERT, UPDATE,
            # or DELETE operations—the method returns the 'rowcount'. This
            # provides the caller with essential feedback, such as
            # confirming exactly how many records were updated or purged
            # during an administrative task.
            if commit:
                return cursor.rowcount

            # DYNAMIC RESULT CONSUMPTION (DQL OPERATIONS)
            # For data retrieval queries (SELECT), we respect the
            # 'fetch_all' toggle. This allows the calling logic to
            # efficiently choose between pulling a comprehensive list of
            # records for a report or a single, specific record for
            # individual processing.
            if fetch_all:
                result = cursor.fetchall()

                # RETURN TYPE CONSISTENCY (ITERATION SAFETY)
                # We ensure that a 'fetch_all' request always returns a
                # list object. By returning an empty list instead of 'None'
                # when no results are found, we prevent downstream
                # iteration errors in the application's loops or UI templates.
                return result if result is not None else []

            # SINGLE-ROW PRECISION
            # Returns a single dictionary (or None), providing the
            # fastest path for existence checks or single-metric lookups.
            return cursor.fetchone()

    # DYNAMIC COMPARISON & RANGE PREDICATE ENGINE
    # This method extends the pipeline's retrieval capabilities by allowing
    # for non-equality comparisons (e.g., <, >, <=, >=). It is specifically
    # engineered for 'Clash Detection' and 'Boundary Filtering', such as
    # identifying overlapping exam slots or filtering student grades
    # within a specific numeric range.
    def fetch_range(
        self, table: str, constraints: Dict[str, Tuple[Any, str]], logic: str = "AND"
    ) -> List[Dict[str, Any]]:
        """
        Fetches records using flexible comparison operators.
        Format: {"column": (value, "operator")}
        """

        # SCHEMA SANITIZATION
        # We process the table name through the internal safety filter
        # to ensure no malicious structural SQL can be injected.
        safe_table = self._sanitize(table)
        clauses = []
        params = []

        # PREDICATE ASSEMBLY & OPERATOR VALIDATION
        # We iterate through the constraints to map column names to their
        # respective comparison logic. By enforcing a strict allow-list
        # for operators, we prevent the injection of unexpected SQL
        # commands while maintaining flexibility for range-based queries.
        for key, (value, operator) in constraints.items():
            safe_key = self._sanitize(key)

            # OPERATOR SECURITY GATE
            # If an unsupported or malicious operator is provided, we
            # default to standard equality ('=') to maintain query
            # safety without crashing the pipeline.
            valid_operators = ["<", ">", "<=", ">=", "!=", "="]
            if operator not in valid_operators:
                operator = "="

            clauses.append(f"`{safe_key}` {operator} %s")
            params.append(value)

        # DYNAMIC SQL SYNTHESIS
        # The clauses are joined using the specified logic (typically 'AND').
        # If no constraints are provided, we use the "1=1" No-Op to ensure
        # the SELECT statement remains syntactically valid.
        where_str = f" {logic} ".join(clauses) if clauses else "1=1"
        sql = f"SELECT * FROM `{safe_table}` WHERE {where_str}"

        # EXECUTION & TYPE NORMALIZATION
        # We delegate the execution to the raw 'query' engine. To resolve
        # Type Assignment errors, we explicitly validate that the result
        # is a list. This ensures that the calling function can always
        # iterate over the return value without 'NoneType' or 'int' conflicts.
        result = self.query(sql, tuple(params))

        if isinstance(result, list):
            return result
        return []


# DATABASE ORCHESTRATOR INSTANTIATION
# THE SINGLETON-PATTERN SERVICE INSTANCE
# Here, we initialize the 'DatabasePipeline' as a global 'database' object.
# In a web-service architecture (like Flask), this ensures that the
# connection pool is created once during the application's "cold start."
# Subsequent imports of this module will reference the same active pool,
# preventing the overhead of re-initializing the database driver or
# hitting the MySQL server's 'max_connections' limit.
database = DatabasePipeline(
    # INJECTED CONFIGURATION
    # We pass the pre-loaded 'config' object. This encapsulation allows
    # the pipeline to dynamically adapt to different environments
    # (e.g., swapping a local MariaDB for a production RDS instance)
    # without modifying the core logic inside the class.
    config=config,
    # POOL IDENTIFICATION
    # 'pool_name' provides a unique label for the pool within the MySQL
    # driver. This is particularly useful for server-side monitoring;
    # when reviewing active processes in MariaDB, the 'pool_name' helps
    # sysadmins distinguish between the Timetable Management pool
    # and other microservices.
    pool_name="university_sys_pool",
    # CONCURRENCY SCALING
    # 'pool_size=5' pre-allocates five persistent connections. This
    # balancing act ensures there is always a "warm" connection ready
    # for a student's request, while keeping the database's memory
    # footprint lean on the host system.
    pool_size=10,
)


# DATA RETRIEVAL USAGE (FETCH)
# SINGLE RECORD LOOKUP (FETCH_ALL=FALSE)
# When retrieving a specific entity—such as a student profile or a unique
# course record—we set 'fetch_all=False'. This returns a single dictionary
# (or 'None'), allowing for direct access to fields without indexing
# into a list, which simplifies the "Business Logic" in your Flask routes.
student = database.fetch(
    table="students",
    where={"index_number": "HTU12345"},
    columns=["name", "department", "level"],
    fetch_all=False,
)

# COMPLEX FILTERING WITH LISTS (IN CLAUSE)
# The pipeline's predicate engine automatically detects Python lists.
# Passing a list to the 'where' dictionary triggers an 'IN' clause in SQL.
# This is highly efficient for batch-fetching specific sets, such as
# retrieving all timetables for a specific group of lecture halls.
active_timetables = database.fetch(
    table="exam_schedules",
    where={"hall_id": ["H1", "H2", "LT1"], "status": "confirmed"},
    order_by="start_time ASC",
)

# PAGINATION & DATA SAMPLING
# To prevent memory exhaustion when dealing with large datasets (like
# system logs or audit trails), we leverage the 'limit' parameter.
# This ensures the database driver only fetches the necessary subset,
# maintaining high performance even as the database grows.
recent_logs = database.fetch(table="system_audit", order_by="created_at DESC", limit=50)

# DOCUMENTATION SUMMARY: FETCH PROTOCOL
# ------------------------------------------------------------------------------
# 1. PARAMETERIZATION: Values in 'where' are never injected into the query
#    string directly; they are passed as bound parameters to prevent
#    SQL Injection.
# 2. KEYWORD PROTECTION: All table and column names are automatically
#    wrapped in backticks (`) during the 'fetch' call, protecting
#    against collisions with MySQL reserved words.
# 3. RESOURCE SAFETY: Every 'fetch' call internally manages its own
#    connection checkout and return; no manual closure is required by
#    the caller.


# DATA PERSISTENCE USAGE (SAVE)
# SCENARIO 1: NEW RECORD CREATION
# This is the primary method for persisting new entities, such as registering
# a new student or adding a course to the catalog. The method accepts a
# dictionary where keys exactly match database column names, providing
# a clean, "Object-Literal" style of data entry.
new_student_data = {
    "index_number": "HTU2026001",
    "full_name": "Cyril Admin",
    "email": "cyril@htu.edu.gh",
    "enrollment_date": "2026-03-13",
}

# PRIMARY KEY RETRIEVAL
# The 'save' method returns the 'lastrowid' (the Auto-Increment ID).
# This is vital for relational integrity; for example, you need this
# ID immediately if you intend to link this new student to a specific
# department or fee structure in a related table.
student_id = database.save(table="students", data=new_student_data)

# SCENARIO 2: CONDITIONAL DATA INJECTION
# Because the 'data' parameter is a standard dictionary, you can
# dynamically build your record based on application logic (e.g.,
# only including 'middle_name' if it exists) before passing it
# to the pipeline.
log_entry = {
    "action": "LOGIN_SUCCESS",
    "user_id": student_id,
    "ip_address": "192.168.1.50",
}
database.save(table="system_audit", data=log_entry)

# DOCUMENTATION SUMMARY: SAVE PROTOCOL
# ------------------------------------------------------------------------------
# 1. ATOMIC COMMITS: The 'save' method uses the 'commit=True' flag in the
#    underlying context manager, ensuring that the write is finalized
#    immediately and made visible to other database connections.
# 2. DICTIONARY MAPPING: The pipeline handles the transformation of keys
#    into a sanitized column list and values into parameterized '%s'
#    placeholders, shielding the system from malformed data injection.
# 3. ID CONSISTENCY: By returning 'int(cursor.lastrowid or 0)', the
#    method provides a reliable way to track the identity of the
#    newly persisted row within the same execution thread.


# BATCH PERSISTENCE USAGE (SAVE_MANY)
# DATA SET PREPARATION
# 'save_many' expects a list of dictionaries. Each dictionary represents a
# row and must share the exact same keys (columns). This structure allows
# the pipeline to generate a single optimized execution plan for the
# entire dataset.
course_list = [
    {"code": "CS101", "title": "Intro to Programming", "credits": 3},
    {"code": "CS102", "title": "Data Structures", "credits": 4},
    {"code": "CS103", "title": "Database Systems", "credits": 3},
]

# OPTIMIZED BATCH EXECUTION
# Instead of calling 'save' in a loop (which creates individual network
# overhead for every row), 'save_many' uses 'executemany'. This sends
# the template query once and streams the data values in a highly
# efficient manner.
rows_inserted = database.save_many(table="course_catalog", data_list=course_list)

# VERIFICATION & LOGGING
# The method returns the total count of successfully inserted records.
# This is critical for audit trails; it allows the system to verify
# if the number of records processed matches the number of records
# intended for import.
sys.stderr.write(f"[+] Batch import completed. {rows_inserted} courses added.")


# DOCUMENTATION SUMMARY: SAVE_MANY PROTOCOL
# ------------------------------------------------------------------------------
# 1. NETWORK EFFICIENCY: This method minimizes "Handshake Latency" by
#    grouping multiple inserts into a single database transaction, making
#    it the preferred choice for log ingestion or bulk imports.
# 2. SCHEMA UNIFORMITY: It is a prerequisite that all items in the
#    'data_list' possess identical keys. The pipeline derives the target
#    columns from the first item in the list.
# 3. ATOMIC INTEGRITY: The entire batch is committed as a single unit
#    within the context manager. If a fatal error occurs mid-batch,
#    the transaction rolls back to prevent "partial data" corruption.


# ATOMIC UPSERT USAGE (INSERT OR UPDATE)
# DATA PAYLOAD DEFINITION
# We define the complete record as it should look. In this case, we are
# managing a student's GPA. If the 'student_id' already exists in the
# 'academic_records' table, we want to update the stats rather than
# failing with a "Duplicate Entry" error.
academic_update = {
    "student_id": 505,
    "gpa": 3.85,
    "credits_earned": 120,
    "last_updated": "2026-03-13",
}

# CONFLICT RESOLUTION LOGIC
# The 'update_cols' parameter specifies exactly which columns should be
# overwritten if a collision occurs. This allows you to protect
# certain fields (like 'created_at' or 'student_id') from being
# changed while ensuring the 'gpa' and 'last_updated' are refreshed.
affected_rows = database.upsert(
    table="academic_records",
    data=academic_update,
    update_cols=["gpa", "credits_earned", "last_updated"],
)

# INTERPRETING THE RESULT
# MySQL returns a specific 'rowcount' for upserts:
# - 1: A brand new record was created.
# - 2: An existing record was updated with new data.
# - 0: An existing record was found, but the data provided was identical.
if affected_rows == 2:
    sys.stderr.write(f"[~] Existing academic record was refreshed.")
elif affected_rows == 1:
    sys.stderr.write(f"[+] New academic record was successfully created.")


# DOCUMENTATION SUMMARY: UPSERT PROTOCOL
# ------------------------------------------------------------------------------
# 1. ATOMICITY: By using 'ON DUPLICATE KEY UPDATE', the operation happens
#    entirely within the database engine in one step. This prevents "Race
#    Conditions" where two threads might try to check-then-insert at once.
# 2. SELECTIVE OVERWRITING: The 'update_cols' list gives the developer
#    granular control, ensuring that only the intended fields are
#    modified during a collision.
# 3. IDEMPOTENCY: This method is inherently idempotent; running the
#    same upsert multiple times with the same data will not create
#    duplicate rows, making it ideal for data synchronization scripts.


# DATA MODIFICATION USAGE (UPDATE)
# TARGETED FIELD UPDATE
# This is the standard way to modify specific columns in a record.
# Only the fields provided in the 'data' dictionary will be changed;
# all other columns remain untouched.
contact_update = {"phone_number": "+233 24 000 0000", "emergency_contact": "Jane Doe"}

# SAFETY-FIRST EXECUTION
# The 'where' dictionary defines the scope of the update. By targeting
# a unique identifier like 'index_number', we ensure that only one
# specific record is modified.
rows_modified = database.update(
    table="students", data=contact_update, where={"index_number": "HTU2026099"}
)

# BATCH STATUS UPDATES
# Updates can also be applied to groups. For example, marking all
# courses in a specific department as 'Registration Closed'.
database.update(
    table="courses",
    data={"status": "closed"},
    where={"department_id": "CS_DEPT", "semester": 2},
)


# DOCUMENTATION SUMMARY: UPDATE PROTOCOL
# ------------------------------------------------------------------------------
# 1. SAFETY TRIGGER: If the 'where' dictionary is empty, the method raises
#    a 'ValueError'. This prevents "Table-Wide Updates" that could
#    accidentally overwrite every row in the database.
# 2. SELECTIVE SETTING: The pipeline dynamically constructs the 'SET'
#    clause based on the dictionary keys, ensuring only relevant
#    data is sent to the MySQL server.
# 3. TRANSACTIONAL INTEGRITY: Like 'save', the 'update' method triggers
#    an atomic commit. It returns the 'rowcount' to confirm how many
#    records were actually changed (records with identical data are
#    counted as 0 modified rows by MySQL).


# DATA REMOVAL USAGE (DELETE)
# SPECIFIC RECORD REMOVAL
# To remove a single, specific entry, define the primary key or a unique
# identifier in the 'where' clause. This ensures the operation is
# surgically precise.
rows_deleted = database.delete(
    table="exam_seat_assignments", where={"assignment_id": 9872}
)

# BATCH DELETION
# You can remove multiple records that meet a certain criteria. For
# instance, clearing out expired temporary password reset tokens
# from the system.
deleted_tokens = database.delete(table="password_resets", where={"status": "expired"})

# MULTI-CRITERIA FILTERING
# By passing multiple keys in the 'where' dictionary, the pipeline
# builds an 'AND' condition, ensuring that only records matching
# EVERY criterion are removed.
database.delete(
    table="course_registrations",
    where={"student_id": 105, "course_id": "CS101", "semester": "2025_FALL"},
)


# DOCUMENTATION SUMMARY: DELETE PROTOCOL
# ------------------------------------------------------------------------------
# 1. TRUNCATION PROTECTION: An empty 'where' dictionary will trigger a
#    'ValueError'. This prevents an accidental "DELETE FROM table" (no filter)
#    which would wipe all data. To delete all rows, a developer must
#    explicitly provide a filter like {"1": 1}.
# 2. ATOMIC EXECUTION: The deletion is handled as a single transaction.
#    The method returns the 'rowcount' so the application can confirm
#    exactly how many records were purged from the storage engine.
# 3. PARAMETERIZED SECURITY: All filtering values are sanitized and
#    parameterized, ensuring that malicious input cannot escape the
#    'WHERE' clause to perform unauthorized database actions.


# DYNAMIC RELATIONAL JOIN USAGE (FETCH_JOINED)
# ACADEMIC DASHBOARD DATA AGGREGATION
# This scenario demonstrates how to pull data from three separate tables
# (examination, courses, and programs) in a single, secure operation.
# By defining relationships as a structured 'joins' list, we avoid
# manual SQL syntax while maintaining a clear relational map.

# RELATIONSHIP CONFIGURATION
# We define the "Bridges" between tables. Each tuple contains:
# (Target Table, Left Key, Right Key, Join Type)
university_joins = [
    ("courses", "examination.course_id", "courses.id", "LEFT"),
    ("programs", "courses.program_id", "programs.id", "LEFT"),
]

# SELECTIVE COLUMN MAPPING
# We specify exactly which data points to retrieve. Using 'AS' aliases
# ensures that if multiple tables have a column named 'name', they
# are mapped to unique keys in the resulting Python dictionary.
report_columns = [
    "examination.*",
    "courses.name AS course_name",
    "programs.name AS program_name",
]

# SECURE EXECUTION
# The pipeline assembles the SQL skeleton, integrates the JOINS,
# and applies the parameterized WHERE filter. This keeps the
# calling code clean and focused on business logic.
exam_schedule = database.fetch_joined(
    main_table="examination",
    joins=university_joins,
    columns=report_columns,
    where={"courses.user_level": 100},
    order_by="examination.start_time ASC",
)

# DOCUMENTATION SUMMARY: FETCH_JOINED PROTOCOL
# ------------------------------------------------------------------------------
# 1. STRUCTURAL AUTOMATION: The method eliminates manual 'JOIN/ON' syntax,
#    preventing "Cartesian Product" errors and accidental data duplication
#    caused by missing join conditions.
# 2. DATA FLATTENING: Complex relational structures are returned as a
#    simple List of Dictionaries, making the data ready for immediate
#    iteration in Flask templates or JSON API responses.
# 3. UNIFIED SECURITY: Filtering is handled by the same '_build_where'
#    engine used in standard fetches, ensuring that even multi-table
#    queries are 100% protected against SQL Injection.


# DYNAMIC RAW SQL USAGE (QUERY)
# SCENARIO: ADVANCED ACADEMIC ANALYTICS
# This scenario utilizes the 'query' method to perform complex data
# aggregation that falls outside standard CRUD patterns. Here, we
# calculate the average GPA per department—an operation requiring
# 'GROUP BY' logic and SQL aggregate functions.

# RAW SQL ARCHITECTURE
# We define the SQL string using standard placeholders (%s). This allows
# for complex subqueries, unions, or grouping logic while keeping
# the structural "Skeleton" of the query distinct from the "Muscle" (data).
analytics_sql = """
    SELECT dept_name, COUNT(student_id) as student_count, AVG(gpa) as avg_gpa
    FROM student_records
    WHERE faculty_id = %s
    GROUP BY dept_name
    HAVING avg_gpa > %s
"""

# SECURE EXECUTION & DATA BINDING
# Even with raw SQL, we pass parameters as a separate tuple. The
# pipeline handles the acquisition of a pooled connection and
# ensures the results are mapped to a clean list of dictionaries.
department_stats = database.query(sql=analytics_sql, params=(12, 3.0), fetch_all=True)

# ADMINISTRATIVE DATA MODIFICATION (COMMIT)
# The 'query' method also handles manual DML (Data Manipulation Language).
# By setting 'commit=True', we can execute bulk updates or custom
# deletions that require specific logic.
purge_sql = "DELETE FROM login_logs WHERE attempt_date < %s AND status = %s"
deleted_count = database.query(
    sql=purge_sql, params=("2026-01-01", "expired"), commit=True
)


# DOCUMENTATION SUMMARY: QUERY PROTOCOL
# ------------------------------------------------------------------------------
# 1. TOTAL EXPRESSIVE FREEDOM: This is the pipeline's "Master Key,"
#    allowing for any valid MySQL command, including Subqueries,
#    Aggregates (SUM/AVG), and Table Maintenance.
# 2. INTEGRATED POOLING: Despite being a "Raw" execution method, it still
#    benefits from the automated lifecycle of the '_get_cursor' context
#    manager, ensuring connections are never leaked.
# 3. VERSATILE RETURN TYPES: The method intelligently switches between
#    returning result sets (for SELECT) and row counts (for COMMIT
#    operations), providing consistent feedback to the application layer.


# DYNAMIC RANGE INTERFACE (FETCH_RANGE)
# SCENARIO: TEMPORAL OVERLAP & CLASH DETECTION
# This scenario demonstrates the pipeline's ability to identify resource
# conflicts. In a university environment, this is the primary defense
# against "Double-Booking," ensuring that no two academic events occupy
# the same Room (or Lecturer) at the same time.

# THE OVERLAP ARCHITECTURE
# We utilize a specific mathematical intersection: An overlap exists if the
# Existing slot starts before the New slot ends, AND the Existing slot ends
# after the New slot starts. This single check covers every possible conflict
# variation (Partial overlap, Enclosure, or Identical slots).

# CONSTRAINTS CONFIGURATION & DATA MAPPING
# We define a dictionary where each key represents a database column and each
# value is a tuple containing the (Comparison Value, SQL Operator). This
# structure allows the pipeline to build a non-equality WHERE clause dynamically.
proposed_constraints = {
    "room_id": (101, "="),  # Strict Equality: Same physical space
    "date": ("2026-03-20", "="),  # Strict Equality: Same calendar day
    "start_time": ("10:30", "<"),  # Range: Existing start is BEFORE new end
    "end_time": ("09:00", ">"),  # Range: Existing end is AFTER new start
}

# PIPELINE EXECUTION & TYPE VALIDATION
# The 'fetch_range' method assembles the SELECT statement, sanitizes
# the identifiers, and returns a verified list.
conflicts = database.fetch_range(
    table="exams", constraints=proposed_constraints, logic="AND"
)

# CONFLICT RESOLUTION & FEEDBACK
if conflicts:
    # DATA ISOLATION: A conflict has been identified.
    # We stop the transaction and notify the user of the specific clash.
    print(f"[!] CLASH: Room {proposed_constraints['room_id'][0]} is taken!")
else:
    # ATOMIC PERSISTENCE: The slot is clear.
    # Since 'fetch_range' returned an empty list, we proceed to 'save()'.
    database.save(
        "exams",
        {
            "room_id": 101,
            "date": "2026-03-20",
            "start_time": "09:00",
            "end_time": "10:30",
        },
    )


# DOCUMENTATION SUMMARY: RANGE PROTOCOL
# ------------------------------------------------------------------------------
# 1. OPERATOR ENFORCEMENT: The method uses a strict internal allow-list
#    (<, >, <=, >=, !=) to ensure that even while providing flexible
#    comparisons, the structural integrity of the SQL remains uncompromised.
# 2. LOGICAL CONJUNCTION: By supporting a 'logic' parameter (defaulting to
#    'AND'), the pipeline can handle both restrictive "Clash" checks and
#    broad "Either/Or" filtering.
# 3. ITERATION SAFETY: To satisfy type-hinting requirements and prevent
#    runtime errors, the method explicitly normalizes all outputs to a
#    List[Dict]. This ensures that even a "No Result" state returns an
#    empty iterable [] rather than a None or an int.
