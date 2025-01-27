import streamlit as st
import os
from groq import Groq
import json
from typing import List, Dict

class TravelChatbot:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.conversation_history = []
        self.user_preferences = {}

    def generate_response(self, user_input: str) -> str:
        conversation_context = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.conversation_history] + 
            [f"User: {user_input}"]
        )

        messages = [
            {
                "role": "system", 
                "content": """
                You are a travel preference collector. Your role is to gather travel preferences through natural conversation.

                REQUIREMENTS:
                1. ALWAYS end your response with a JSON object containing newly learned preferences
                2. Keep responses conversational but focused on gathering information
                3. Ask only ONE question at a time
                4. Do not generate itineraries or detailed plans

                JSON FORMAT:
                - Must be the last part of your response
                - Must be a valid JSON object
                - Only include newly learned information
                - Use clear, consistent keys
                
                Example response:
                "I see you're interested in visiting Bali! When are you planning to travel?
                {"destination": "Bali"}
                
                Common preference keys:
                - destination
                - duration
                - budget
                - accommodation_type
                - interests
                - travel_style
                - dining_preferences
                - transportation
                """
            },
            {
                "role": "system", 
                "content": f"Current preferences: {json.dumps(self.user_preferences, indent=2)}"
            },
            {
                "role": "user", 
                "content": conversation_context
            }
        ]

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )
        
        return response.choices[0].message.content

    def update_preferences(self, response: str) -> None:
        """Update preferences from the AI response."""
        try:
            # Find the last occurrence of a JSON object
            last_brace_start = response.rstrip().rfind('{')
            last_brace_end = response.rstrip().rfind('}')
            
            if last_brace_start != -1 and last_brace_end != -1:
                json_str = response[last_brace_start:last_brace_end + 1]
                preference_update = json.loads(json_str)
                
                # Only update if we got a valid dictionary with non-empty values
                if isinstance(preference_update, dict) and preference_update:
                    self.user_preferences.update({
                        k: v for k, v in preference_update.items() 
                        if v is not None and str(v).strip()
                    })
        except Exception as e:
            print(f"Error updating preferences: {e}")

    def process_user_input(self, user_input: str) -> str:
        self.conversation_history.append({
            "role": "user", 
            "content": user_input
        })

        ai_response = self.generate_response(user_input)

        # Extract the conversational part (everything before the JSON)
        last_brace_start = ai_response.rstrip().rfind('{')
        conversational_response = ai_response[:last_brace_start].strip() if last_brace_start != -1 else ai_response

        self.conversation_history.append({
            "role": "assistant", 
            "content": conversational_response
        })

        self.update_preferences(ai_response)

        return conversational_response

    def generate_itinerary(self) -> str:
        itinerary_prompt = f"""
        COMPREHENSIVE TRAVEL EXPERIENCE DESIGN

        Traveler Preferences:
        {json.dumps(self.user_preferences, indent=2)}

        ITINERARY GENERATION PROTOCOL:
        1. Craft a narrative-driven, immersive travel experience
        2. Balance structured activities with flexible exploration
        3. Integrate local cultural insights
        4. Provide logistical and experiential details

        DETAILED REQUIREMENTS:
        - Hour-by-hour activity breakdown
        - Cultural context for each experience
        - Hidden local recommendations
        - Practical travel tips
        - Estimated costs and time allocations
        - Alternative activity options
        - Transportation and mobility considerations

        OUTPUT FORMAT:
        - Day-by-day narrative
        - Thematic experience progression
        - Insider local knowledge
        - Personalized recommendations
        """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a master travel experience architect."},
                {"role": "user", "content": itinerary_prompt}
            ],
            temperature=0.7,
            max_tokens=20000
        )
        
        return response.choices[0].message.content

def initialize_session_state():
    if 'chatbot' not in st.session_state:
        api_key = "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"
        st.session_state.chatbot = TravelChatbot(api_key)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    if 'show_itinerary' not in st.session_state:
        st.session_state.show_itinerary = False

def main():
    st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
    
    st.title("🌎 AI Travel Planner")
    st.markdown("""
    Let me help you plan your perfect trip! Share your travel dreams and preferences, 
    and I'll create a personalized itinerary for you.
    """)

    initialize_session_state()

    # Sidebar with current preferences and generate button
    with st.sidebar:
        st.header("📋 Current Travel Preferences")
        
        # Debug information
        st.write("Debug Info:")
        st.write(f"Number of preferences: {len(st.session_state.chatbot.user_preferences)}")
        st.write("Current preferences:", st.session_state.chatbot.user_preferences)
        
        if st.session_state.chatbot.user_preferences:
            for key, value in st.session_state.chatbot.user_preferences.items():
                st.write(f"**{key}:** {value}")
            
            # Modified preference check
            preference_count = len(st.session_state.chatbot.user_preferences)
            st.write(f"Collected {preference_count} preferences out of 4 required")
            
            if preference_count >= 4:
                st.write("---")
                st.write("Ready to generate your itinerary!")
                if st.button("Generate Itinerary", key="generate_button"):
                    st.session_state.show_itinerary = True
                    st.write("Itinerary generation triggered!")  # Debug info
        else:
            st.write("No preferences collected yet. Start chatting to build your travel profile!")
        
        st.write("---")
        if st.button("Start New Planning Session"):
            st.session_state.clear()
            st.experimental_rerun()

    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Generate and display itinerary if requested
        if st.session_state.show_itinerary:
            with st.chat_message("assistant"):
                st.write("Generating itinerary...")  # Debug info
                with st.spinner("Creating your perfect trip itinerary..."):
                    itinerary = st.session_state.chatbot.generate_itinerary()
                    st.markdown("## Your Personalized Travel Itinerary")
                    st.markdown(itinerary)
                    # Reset the show_itinerary flag
                    st.session_state.show_itinerary = False
                    # Add the itinerary to the message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"## Your Personalized Travel Itinerary\n\n{itinerary}"
                    })

        # Handle new user input
        if user_input := st.chat_input("Tell me about your travel plans..."):
            with st.chat_message("user"):
                st.markdown(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                response = st.session_state.chatbot.process_user_input(user_input)
                # Debug info for preference update
                st.write("Before preference update:", st.session_state.chatbot.user_preferences)
                st.markdown(response)
                st.write("After preference update:", st.session_state.chatbot.user_preferences)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()