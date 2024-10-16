import os
import openai
import pandas as pd
import streamlit as st
from llama_index.core import SQLDatabase
from llama_index.core import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.openai import OpenAI
from prompts import DEFAULT_TEXT_TO_SQL_TMPL
from utils import create_table_from_dataframe
from sqlalchemy import create_engine, MetaData

st.session_state["table_names"] = []

openai.api_key = os.environ.get("OPENAI_API_KEY")


def main():
    # Set the title of the app
    st.title("SQL Retriever Test")

    st.write(
        """
    ## Upload a CSV file to perform basic analysis
    """
    )

    # File uploader widget
    uploaded_files = st.file_uploader("Choose a CSV file", type=["csv"], accept_multiple_files=True)

    if uploaded_files is not None:
        try:
            table_names = st.session_state["table_names"]
            engine = create_engine("sqlite:///:memory:")
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                _, file_name = os.path.split(uploaded_file.name)
                table_name, _ = file_name.split(".")
                metadata_obj = MetaData()
                create_table_from_dataframe(df, table_name, engine, metadata_obj)
                table_names.append(table_name)
            st.session_state["table_names"] = table_names
            sql_database = SQLDatabase(engine, include_tables=table_names)
            llm = OpenAI(temperature=0.001, model="gpt-4o-mini-2024-07-18")
            DEFAULT_TEXT_TO_SQL_PROMPT = PromptTemplate(
                DEFAULT_TEXT_TO_SQL_TMPL,
                prompt_type=PromptType.TEXT_TO_SQL,
            )
            query_engine = NLSQLTableQueryEngine(
                sql_database=sql_database, tables=table_names, text_to_sql_prompt=DEFAULT_TEXT_TO_SQL_PROMPT, llm=llm
            )
            query_str = st.text_input("Enter your query here")
            submit_button = st.button("Submit")
            if submit_button:
                if not query_str:
                    st.write("Please enter a valid query")
                else:
                    response = query_engine.query(query_str)
                    st.write(response.response)
                    st.write("SQL Query:", response.metadata["sql_query"])
                    result_df = pd.DataFrame(response.metadata["result"], columns=response.metadata["col_keys"])
                    st.dataframe(result_df)

        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

    else:
        st.info("Awaiting CSV file upload.")


if __name__ == "__main__":
    main()
