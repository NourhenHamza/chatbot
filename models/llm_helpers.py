import os
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_community.llms import LlamaCpp
from langchain_groq import ChatGroq

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.schema import BaseOutputParser
from langchain.docstore.document import Document


class CommaSeparatedListOutputParser(BaseOutputParser):
    """Parse the output of an LLM call to a comma-separated list."""

    def parse(self, text: str):
        """Parse the output of an LLM call."""
        return text.strip().split(", ")


def convert_to_documents(data_list):
    data = []
    for data_dict in data_list:
        list_value = list(data_dict.keys())[0]
        # metadata = {"source": data_dict[list_value]}
        metadata = data_dict
        data.append(Document(page_content=str(data_dict[list_value]), metadata=metadata))
    return data


class LanguageModelRequest:
    """ 
    A class to handle requests to a language model using Groq with Llama.
    
    This class provides methods to send questions to a language model and retrieve responses.
    """

    def __init__(self):
        # Using GROQ_API_KEY instead of OpenAI
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.chat_model = ChatGroq(
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",  # Using Llama model
            groq_api_key=groq_api_key,
            temperature=0
        )
        self.system_prompt = os.getenv("SYSTEM_PROMPT", "You are an AI who give information from given data")
        self.system_prompt_query = os.getenv("SYSTEM_PROMPT_QUERY", "You are an AI that creates database queries based on user questions and database schema.")
        self.compressor = LLMChainExtractor.from_llm(llm=self.chat_model)

    def ask_llm(self, question, data_list):
        """ 
        Send a question with data to llm and get the response.

        """
        docs = convert_to_documents(data_list)

        data = docs
        template = self.system_prompt + "\ndata: {data} \n\nBased on the provided data, give a concise and natural language response without any special formatting characters like \n or \t. Focus on providing a human-like answer."
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "{questions}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chat_prompt.format_messages(data=data, questions=question)

        chain = LLMChain(
            llm=self.chat_model,
            prompt=chat_prompt,
            # output_parser=CommaSeparatedListOutputParser() # Removed this as we want natural language, not a comma-separated list
        )

        response = chain.run(data=data, questions=question)
        return response.replace('\n', ' ').replace('\t', ' ').strip() # Post-process to remove newlines and tabs

    def generate_query_by_llm(self, tables_schema, query):
        template = self.system_prompt_query + (
            "\nDatabase Schema: {tables_schema}\n\nGenerate a SQL query based on the user\'s question and the provided database schema. Only output the SQL query, no other text. Ensure the query is valid for the given schema. If the user asks for available tables or collections, generate a query to list them (e.g., SELECT table_name FROM information_schema.tables WHERE table_schema = \'your_database_name\'; for SQL or db.listCollectionNames() for MongoDB). If the user asks for information about the database or its contents, generate a relevant query. If no specific query is needed, return an empty string.")
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "{questions}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chat_prompt.format_messages(tables_schema=tables_schema, questions=query)

        chain = LLMChain(
            llm=self.chat_model,
            prompt=chat_prompt,
            output_parser=CommaSeparatedListOutputParser()
        )

        response = chain.run(tables_schema=tables_schema, questions=query)
        return response[0].strip()

    def get_table_based_on_query(self, tables_schema, query):
        template = ("Based on the user\'s question and the provided database schema, identify the most relevant table name. Only output the table name, no other text. If multiple tables are relevant, choose the primary one. If no specific table is relevant, return an empty string.\nDatabase Schema: {tables_schema}")
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "{questions}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chat_prompt.format_messages(tables_schema=tables_schema, questions=query)

        chain = LLMChain(
            llm=self.chat_model,
            prompt=chat_prompt,
            output_parser=CommaSeparatedListOutputParser()
        )

        response = chain.run(tables_schema=tables_schema, questions=query)
        return response[0].strip()

    def get_column_based_on_query(self, columns, query):
        template = ("Get the column names for sql query based on given columns and question only write column names "
                    "so it can use for query database\ncolumns: {columns}")
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "{questions}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chat_prompt.format_messages(columns=columns, questions=query)

        chain = LLMChain(
            llm=self.chat_model,
            prompt=chat_prompt,
            output_parser=CommaSeparatedListOutputParser()
        )

        response = chain.run(columns=columns, questions=query)
        return response[0]
