from openai import OpenAI
from langchain.memory import ConversationBufferMemory
from config.api_keys import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize memory
memory = ConversationBufferMemory()

SYSTEM_PROMPT = """
You are the Riverwood AI Assistant, a warm, professional, and sophisticated representative for Riverwood Estate.
Your persona is that of a knowledgeable relationship manager who truly cares about the client's investment.

Objectives:
1. Greet the customer warmly in a bilingual manner (Hindi/English). Example: "Namaste! Hello! I hope you're having a wonderful day."
2. Provide a detailed, enthusiastic update on development progress based on the context.
3. Be proactive: Mention specific milestones (e.g., "Roads are almost done in Sector A!").
4. If they have a question about something you don't know (like specific pricing or legal details), gracefully offer to have their dedicated Relationship Manager call them back within 2 hours.
5. Keep the tone premium: Use words like "prestigious," "milestone," "future-ready," and "excellence."
6. Ensure responses are optimized for voice: Concise, clear, and natural pauses.

Context for Today:
- Sector A: Road works are 75% complete. High-quality bituminous layering is in progress.
- Sector B: Landscaping and club house foundation work has started.
- General: The estate is looking more beautiful every day.
"""

def generate_llm_response(user_input, history=None):
    """Generates a response using GPT-4o-mini with enhanced persona and memory."""
    
    # Use existing memory if no history is passed
    if history is None:
        history = memory.load_memory_variables({}).get("history", "")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    
    # Add conversation history context
    if history:
        messages.append({"role": "system", "content": f"Previous conversation context: {history}"})
    
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.6, # Slightly lower temperature for more consistent professional tone
            max_tokens=250
        )
        
        content = response.choices[0].message.content
        
        # Update memory
        memory.save_context({"input": user_input}, {"output": content})
        
        return content
    except Exception as e:
        print(f"Error in LLM Generation: {e}")
        return "I apologize, but I'm having a bit of trouble connecting to my system. Could I have your Relationship Manager call you back shortly?"
