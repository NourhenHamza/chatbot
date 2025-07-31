import os
from sqlalchemy import MetaData, Table, text


class DynamicDatabase:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.engine = None
        self.connection = None
        self.db_type = os.environ.get("DATABASE_TYPE").lower() if os.environ.get("DATABASE_TYPE") else None
        self.current_db_type = None  # Track the currently connected database type
        self.use_mock_data = os.environ.get("USE_MOCK_DATA", "True").lower() == "true"
        self._schema_cache = {}  # Cache for schema information

    def set_mock_data(self, value):
        self.use_mock_data = value
        # Clear schema cache when switching between mock and real data
        self._schema_cache = {}

    def connect(self):
        """Establish a connection to the specified database using environment variables."""
        # Check if we're already connected to the same database type
        if self._is_connected_to_current_db_type():
            return  # Already connected

        # Close existing connections if switching database types
        self._close_connections()

        try:
            if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
                connection_string = self._get_sql_connection_string()
                print(f"Connecting to {self.db_type}: {connection_string}")
                self._import_sqlalchemy()
                self.engine = sqlalchemy.create_engine(connection_string)
                self.connection = self.engine.connect()
                print(f"{self.db_type.capitalize()} connection successful!")
            elif self.db_type == "mongodb":
                self.connection = self._get_mongodb_connection()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            # Check if connection was successful
            if self.connection is None:
                raise ValueError("Failed to establish database connection.")
            
            # Update the current database type after successful connection
            self.current_db_type = self.db_type
            # Clear schema cache when connecting to a new database
            self._schema_cache = {}
                
        except Exception as e:
            print(f"Connection failed for {self.db_type}: {str(e)}")
            # Reset connection objects on failure
            self.connection = None
            self.engine = None
            raise ValueError(f"Failed to connect to {self.db_type}: {str(e)}")

    def _is_connected_to_current_db_type(self):
        """Check if we're already connected to the current database type."""
        # Check if we're switching database types
        if self.current_db_type != self.db_type:
            return False
            
        if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
            return self.connection is not None and self.engine is not None
        elif self.db_type == "mongodb":
            return self.connection is not None
        return False

    def _close_connections(self):
        """Close existing database connections."""
        try:
            if self.connection is not None:
                if self.current_db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
                    self.connection.close()
                # MongoDB connections don't need explicit closing in the same way
            if self.engine is not None:
                self.engine.dispose()
        except Exception as e:
            print(f"Warning: Error closing previous connections: {str(e)}")
        finally:
            self.connection = None
            self.engine = None
            self.current_db_type = None
            self._schema_cache = {}

    def _get_sql_connection_string(self):
        """Generate an SQL connection string based on the database type and environment variables."""
        user = os.environ.get(f"{self.db_type.upper()}_USER", "")
        password = os.environ.get(f"{self.db_type.upper()}_PASSWORD", "")
        host = os.environ.get(f"{self.db_type.upper()}_HOST", "")
        port = os.environ.get(f"{self.db_type.upper()}_PORT", "")
        dbname = os.environ.get(f"{self.db_type.upper()}_DBNAME", "")

        # Validate required fields
        if not host and self.db_type != "sqlite":
            raise ValueError(f"Missing {self.db_type.upper()}_HOST environment variable")
        if not dbname:
            raise ValueError(f"Missing {self.db_type.upper()}_DBNAME environment variable")

        if self.db_type == "mysql":
            self._import_pymysql()
            if not port:
                port = "3306"  # Default MySQL port
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
        elif self.db_type == "postgresql":
            self._import_psycopg2()
            if not port:
                port = "5432"  # Default PostgreSQL port
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        elif self.db_type == "oracle":
            self._import_cx_oracle()
            if not port:
                port = "1521"  # Default Oracle port
            return f"oracle+cx_oracle://{user}:{password}@{host}:{port}/{dbname}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{dbname}"

    def _get_mongodb_connection(self):
        """Establish a connection to MongoDB using environment variables.
        Supports both local MongoDB and MongoDB Atlas connections.
        """
        self._import_pymongo()
        user = os.environ.get("MONGODB_USER")
        password = os.environ.get("MONGODB_PASSWORD")
        host = os.environ.get("MONGODB_HOST")
        port = os.environ.get("MONGODB_PORT")
        dbname = os.environ.get("MONGODB_DBNAME")

        # Determine connection type based on host
        if host and ('mongodb.net' in host or 'mongodb.com' in host or host.endswith('.mongodb.net')):
            # MongoDB Atlas connection (mongodb+srv)
            if user and password:
                connection_string = f"mongodb+srv://{user}:{password}@{host}/{dbname}"
            else:
                connection_string = f"mongodb+srv://{host}/{dbname}"
            print(f"Connecting to MongoDB Atlas: {connection_string.replace(password, '***') if password else connection_string}")
        else:
            # Local MongoDB connection (mongodb://)
            if user and password:
                connection_string = f"mongodb://{user}:{password}@{host}:{port}/{dbname}"
            else:
                connection_string = f"mongodb://{host}:{port}/{dbname}"
            print(f"Connecting to local MongoDB: {connection_string.replace(password, '***') if password else connection_string}")
        
        try:
            client = MongoClient(connection_string)
            # Test the connection
            client.admin.command('ping')
            print("MongoDB connection successful!")
            return client[dbname]
        except Exception as e:
            print(f"MongoDB connection failed: {str(e)}")
            raise

    # Conditional imports for necessary libraries
    def _import_sqlalchemy(self):
        global sqlalchemy
        import sqlalchemy

    def _import_pymysql(self):
        import pymysql

    def _import_psycopg2(self):
        import psycopg2

    def _import_cx_oracle(self):
        import cx_oracle

    def _import_pymongo(self):
        global MongoClient
        from pymongo import MongoClient

    # Methods related to mock database data for chatbot demo
    @property
    def data(self):
        return {
            "users": [
                {"id": 1, "name": "Alice", "age": 25},
                {"id": 2, "name": "Bob", "age": 30},
                {"id": 3, "name": "Charlie", "age": 35},
            ],
            "orders": [
                {"id": 1, "user_id": 1, "product": "Laptop", "quantity": 1},
                {"id": 2, "user_id": 2, "product": "Phone", "quantity": 2},
                {"id": 3, "user_id": 3, "product": "Tablet", "quantity": 3},
            ]
        }

    def get_tables(self):
        try:
            if self.use_mock_data:
                return list(self.data.keys())

            # Check cache first
            cache_key = f"{self.db_type}_tables"
            if cache_key in self._schema_cache:
                return self._schema_cache[cache_key]

            # Ensure we have a connection to the current database type
            if not self._is_connected_to_current_db_type():
                self.connect()

            if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
                # Ensure sqlalchemy is imported before using it
                self._import_sqlalchemy()
                # Check if engine is still None after connection attempt
                if self.engine is None:
                    raise ValueError(f"Database engine is not initialized for {self.db_type}")
                # Use SQLAlchemy introspection to get table names
                tables = sqlalchemy.inspect(self.engine).get_table_names()
                self._schema_cache[cache_key] = tables
                return tables

            elif self.db_type == "mongodb":
                if self.connection is None:
                    raise ValueError("MongoDB connection is not established")
                collections = self.connection.list_collection_names()
                self._schema_cache[cache_key] = collections
                return collections

            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

        except Exception as e:
            raise ValueError(f"Error fetching table names: {str(e)}")

    def get_fields(self, table_name):
        try:
            if self.use_mock_data:
                if table_name in self.data:
                    return list(self.data[table_name][0].keys())
                return []

            # Check cache first
            cache_key = f"{self.db_type}_{table_name}_fields"
            if cache_key in self._schema_cache:
                return self._schema_cache[cache_key]

            # Ensure we have a connection to the current database type
            if not self._is_connected_to_current_db_type():
                self.connect()

            if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
                # Ensure sqlalchemy is imported before using it
                self._import_sqlalchemy()
                # Check if engine is still None after connection attempt
                if self.engine is None:
                    raise ValueError(f"Database engine is not initialized for {self.db_type}")
                # Use SQLAlchemy introspection to get column names
                columns = sqlalchemy.inspect(self.engine).get_columns(table_name)
                field_names = [column['name'] for column in columns]
                self._schema_cache[cache_key] = field_names
                return field_names

            elif self.db_type == "mongodb":
                if self.connection is None:
                    raise ValueError("MongoDB connection is not established")
                # MongoDB doesn't have "fields" like SQL, but it has document keys.
                # Let's fetch the first document to get its keys.
                document = self.connection[table_name].find_one()
                field_names = list(document.keys()) if document else []
                self._schema_cache[cache_key] = field_names
                return field_names
            return []

        except Exception as e:
            raise ValueError(f"Error fetching fields for table {table_name}: {str(e)}")

    def get_database_name(self):
        """Get the current database name."""
        try:
            if self.use_mock_data:
                return "mock_database"
            
            if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
                return os.environ.get(f"{self.db_type.upper()}_DBNAME", "unknown")
            elif self.db_type == "mongodb":
                return os.environ.get("MONGODB_DBNAME", "unknown")
            else:
                return "unknown"
        except Exception as e:
            print(f"Error getting database name: {str(e)}")
            return "unknown"

    def query(self, table_name, field=None, target_query=None):
        try:
            print(f"DEBUG: query called with table_name='{table_name}', field='{field}', target_query='{target_query}'")
            
            if self.use_mock_data:
                return self._query_mock_data(table_name, field)
            return self._query_real_data(table_name, field, target_query)
        except Exception as e:
            print(f"ERROR in query method: {str(e)}")
            raise ValueError(f"Error querying data for table {table_name}: {str(e)}")

    def _query_mock_data(self, table_name, field=None):
        if table_name in self.data:
            if field:
                return [entry[field] for entry in self.data[table_name]]
            return self.data[table_name]
        return []

    def _query_real_data(self, table_name, field=None, target_query=None):
        if self.connection is None:
            self.connect()
        if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
            return self._query_sql_data(table_name, field, target_query)
        elif self.db_type == "mongodb":
            return self._query_mongodb_data(table_name, field)
        return []

    def _query_sql_data(self, table_name=None, field=None, targeted_query=None):
        # Ensure sqlalchemy is imported before using it
        self._import_sqlalchemy()
        
        metadata = MetaData()
        print(targeted_query)

        if targeted_query and targeted_query.strip():
            # Handle special queries for listing tables or database info
            if "information_schema.tables" in targeted_query.lower():
                # Replace placeholder with actual database name
                db_name = self.get_database_name()
                targeted_query = targeted_query.replace("'your_database_name'", f"'{db_name}'")
                targeted_query = targeted_query.replace("your_database_name", db_name)
            
            # Use the connection object for execution
            with self.engine.connect() as connection:
                result_proxy = connection.execute(text(targeted_query))
                columns = result_proxy.keys()  # get all the columns names from the result proxy
                result = result_proxy.fetchall()
                print(result)
        else:
            # Fallback to simple SELECT * query
            if not table_name:
                return []
                
            metadata.reflect(only=[table_name], bind=self.engine)
            table = metadata.tables[table_name]

            if field:
                # Only select the specified field
                query = table.select().with_only_columns([table.c[field]])
                columns = [field]
            else:
                # Select all columns
                query = table.select()
                columns = table.columns.keys()  # get all the columns names

            # Use the connection object for execution
            with self.engine.connect() as connection:
                result = connection.execute(query).fetchall()

        # Explicitly convert each row to a dictionary
        print(result)
        rows = []
        for row in result:
            row_data = {}
            for column, value in zip(columns, row):
                row_data[column] = value
            rows.append(row_data)

        return rows

    def _query_mongodb_data(self, table_name, field=None):
        collection = self.connection[table_name]
        result = list(collection.find())
        if field:
            return [entry[field] for entry in result]
        return result
