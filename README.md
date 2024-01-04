# LLMOps Chatbot
I created a Langchain-based RAG app where users can ask questions about LLM in Production. The knowledge is scraped from transcripts of the three "LLM in Production" Conferences playlists on Youtube by The MLOps Community.

My aim is to be able to interact with an up-to-date knowledge base of LLMs, a topic that is moving too fast for me to personally keep up.

Key highlights of the project include:
- Scraped transcripts of total 125 videos over 3 playlists from Youtube
- Created a simple RAG application using Langchain for question answering
- Deployed the app on Streamlit

## Future to-dos
- try automatic notes generator -> DB
- clean transcript (just content and no speech yeedee yaadaa)
- include metadata (speaker, date/session?)
- better similarity search: mmr?