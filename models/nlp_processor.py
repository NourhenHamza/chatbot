class NLPQueryProcessor:
    def __init__(self, database, language_model_processor):
        self.database = database
        self.llm = language_model_processor

    def understand_query(self, query):
        """
        Understand the user query and generate appropriate database query.
        Returns table_name, field, and target_query.
        """
        try:
            # Get database schema information
            tables_schema = self._get_database_schema()
            
            # Use LLM to identify the relevant table
            target_table = self.llm.get_table_based_on_query(tables_schema, query)
            
            # Generate the appropriate SQL query
            target_query = self.llm.generate_query_by_llm(tables_schema, query)
            
            # For field, we'll set it to None as we're using full queries now
            target_field = None
            
            print(f"DEBUG: Schema used: {tables_schema}")
            print(f"DEBUG: Target table: {target_table}")
            print(f"DEBUG: Generated query: {target_query}")
            
            return target_table, target_field, target_query
            
        except Exception as e:
            print(f"ERROR in understand_query: {str(e)}")
            # Fallback to first available table if there's an error
            tables = self.database.get_tables()
            if tables:
                return tables[0], None, f"SELECT * FROM {tables[0]}"
            return None, None, None

    def _get_database_schema(self):
        """
        Get comprehensive database schema information including table names,
        column names, and data types.
        """
        try:
            tables = self.database.get_tables()
            schema_info = {}
            
            for table in tables:
                try:
                    fields = self.database.get_fields(table)
                    schema_info[table] = fields
                except Exception as e:
                    print(f"Warning: Could not get fields for table {table}: {str(e)}")
                    schema_info[table] = []
            
            # Format schema information for LLM
            schema_text = f"Database: {self.database.db_type}\n"
            schema_text += f"Available tables: {', '.join(tables)}\n\n"
            
            for table, fields in schema_info.items():
                schema_text += f"Table '{table}' columns: {', '.join(fields) if fields else 'No columns available'}\n"
            
            return schema_text
            
        except Exception as e:
            print(f"ERROR getting database schema: {str(e)}")
            return "No schema information available"
