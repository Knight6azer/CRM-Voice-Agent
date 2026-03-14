from openai import OpenAI
from langchain.memory import ConversationBufferMemory
from config.api_keys import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize memory
memory = ConversationBufferMemory()

SYSTEM_PROMPT = """
You are the Riverwood AI Assistant, a warm and professional representative for Riverwood Estate.
Your goal is to call customers with updates on their plot purchase or construction progress.

Guidelines:
1. Greet naturally in Hindi and English (e.g., "Namaste! Hello!").
2. Provide a polite and warm update aboutdevelopment progress.
3. Ask if they plan to visit the site soon.
4. Record their response intelligently.
5. If they ask a question you don't have the data for, promise a follow-up from their relationship manager.
6. Keep responses concise and conversational for voice interaction.

Example Context:
- Sector A: Road development is 70% complete.
- Sector B: Final landscaping has started.
"""

def generate_llm_response(user_input, history=""):
    """Generates a response using GPT-4o-mini with context awareness."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    
    # Add memory/history if available
    if history:
        messages.append({"role": "assistant", "content": f"Previous conversation: {history}"})
    
    messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    
    content = response.choices[0].message.content
    
    # Update memory
    memory.save_context({"input": user_input}, {"output": content})
    
    return content
