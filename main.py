import os
import streamlit as st

from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma, FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# For Chroma on Streamlit
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

def get_file_names(path_transcripts:str):
    # List all directories in the 'transcripts' folder
    subdirs = [d for d in os.listdir(path_transcripts) if os.path.isdir(os.path.join(path_transcripts, d))]

    all_file_names = []
    for subdir in subdirs:
        subdir_path = os.path.join(path_transcripts, subdir)
        file_names = os.listdir(subdir_path)
        # Optionally, prepend the subdir to the file names if you need the relative path
        file_names = [os.path.join(subdir, f) for f in file_names]
        all_file_names.extend(file_names)

    return all_file_names

def load_docs(path_transcripts:str, file_names:list):
    docs = []
    for file_name in file_names:
        loader = TextLoader(f"{path_transcripts}/{file_name}")
        doc = loader.load()
        docs.extend(doc)
    return docs

def create_chunks(docs, chunk_size:int=1000, chunk_overlap:int=50):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(docs)
    return chunks

def create_or_load_vectorstore(chunks: list, api_key:str) -> Chroma:
    embeddings = OpenAIEmbeddings(openai_api_key=api_key) #HuggingFaceInstructEmbeddings()

    path_vectordb = "./chroma"
    if not os.path.exists(path_vectordb):
        print("CREATING DB")
        vectorstore = Chroma.from_documents(
            chunks, embeddings, persist_directory=path_vectordb
        )
        vectorstore.save_local(path_vectordb)
    else:
        print("LOADING DB")
        #vectorstore = FAISS.load_local(path_vectordb, embeddings)
        vectorstore = Chroma(persist_directory=path_vectordb, embedding_function=embeddings)
        
    return vectorstore

def get_conversation_chain(vectordb:FAISS, api_key=str) -> ConversationalRetrievalChain:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'
    )
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=vectordb.as_retriever(),
        memory=memory,
        return_source_documents=True
    )
    return conversation_chain

def handle_style_and_responses(user_question: str) -> None:
    """
    Handle user input to create the chatbot conversation in Streamlit

    Args:
        user_question (str): User question
    """
    response = st.session_state.conversation({"question": user_question})
    st.session_state.chat_history = response["chat_history"]

    human_style = "background-color: #e6f7ff; border-radius: 10px; padding: 10px;"
    chatbot_style = "background-color: #f9f9f9; border-radius: 10px; padding: 10px;"

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.markdown(
                f"<p style='text-align: right;'><b>User</b></p> <p style='text-align: right;{human_style}'> <i>{message.content}</i> </p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<p style='text-align: left;'><b>Chatbot</b></p> <p style='text-align: left;{chatbot_style}'> <i>{message.content}</i> </p>",
                unsafe_allow_html=True,
            )

if __name__ == "__main__":
    # Load and preprocess data
    path_transcripts = "./transcripts"
    file_names = get_file_names(path_transcripts)
    docs = load_docs(path_transcripts, file_names)
    chunks = create_chunks(docs, 1000, 50)

    # Streamlit UI setup
    st.set_page_config(
        page_title="LLMOps Chatbot",
        page_icon=":llama:",
    )
    st.title("LLMOps Chatbot")
    st.subheader("Ask about LLM in Production")
    st.markdown(
        """
        This chatbot was created to answer questions about the three conferences of LLM in Production organized by MLOps Community.
        """
    )
    st.image("images/Final-Virtual-Conference-1920-1080px-3--06b07788-ae60-4e91-a57a-b319a09a8deb-1693317630137.png")

    # Input for OpenAI API Key
    openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
    
    if openai_api_key:
        # Create Streamlit state variables to prevent erasing history of interaction
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = create_or_load_vectorstore(chunks, openai_api_key)
        if "conversation" not in st.session_state:
            st.session_state.conversation = None
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = None

        user_question = st.text_input("Ask your question")
        with st.spinner("Processing..."):
            if user_question:
                handle_style_and_responses(user_question)

        # create conversation chain
        st.session_state.conversation = get_conversation_chain(
            st.session_state.vector_store, openai_api_key
        )