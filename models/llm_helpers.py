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

    def generate_conversation_title(self, messages):
        """
        Generate a conversation title based on the messages content.
        
        Args:
            messages: List of message dictionaries with 'content' and 'sender' keys
            
        Returns:
            A concise title for the conversation
        """
        if not messages:
            return "Nouvelle conversation"
        
        # Get the first few user messages to understand the topic
        user_messages = [msg['content'] for msg in messages if msg.get('sender') == 'user']
        
        if not user_messages:
            return "Nouvelle conversation"
        
        # Use the first 2-3 user messages to generate a title
        context = " ".join(user_messages[:3])
        
        template = ("Based on the following conversation messages, generate a short, descriptive and unique title (maximum 5-7 words) that captures the main topic, key entities (like patient names, order numbers, product names), or the primary question being discussed. The title should be in English and professional. Prioritize specific details over generic terms. Only return the title, no other text.\n\nMessages: {context}")
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "Generate a title for this conversation."
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        chain = LLMChain(
            llm=self.chat_model,
            prompt=chat_prompt
        )

        try:
            response = chain.run(context=context)
            # Clean up the response and ensure it's not too long
            title = response.strip().replace('"', '').replace("'", "")
            if len(title) > 50:
                title = title[:47] + "..."
            return title if title else "Nouvelle conversation"
        except Exception as e:
            print(f"Error generating conversation title: {e}")
            return "Nouvelle conversation"

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
