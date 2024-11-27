# File: llm_interface.py
import openai
import os
from typing import Dict, List
import json
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

class LLMDecisionMaker:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=self.api_key)
        self.conversation_history = []

    def make_decision(self, context: Dict) -> Dict:
        prompt = self._create_prompt(context)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI controlling a Sim character in a simulation game. You make decisions based on the Sim's needs, surroundings, and previous actions. Respond in JSON format with 'action', 'target', and 'thought' fields."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            decision = json.loads(response.choices[0].message.content)
            
            # Log the full context and response
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'prompt': prompt,
                'response': response.choices[0].message.content,
                'decision': decision
            }
            
            # Create llm_logs directory if it doesn't exist
            os.makedirs('logs/llm_logs', exist_ok=True)
            
            # Save detailed log to separate JSON file
            with open(f'logs/llm_logs/llm_decision_{int(time.time())}.json', 'w') as f:
                json.dump(log_entry, f, indent=4)
            
            self.conversation_history.append({
                "context": context,
                "decision": decision
            })
            return decision
        except Exception as e:
            print(f"Error in LLM decision making: {e}")
            return {"action": "idle", "target": None, "thought": "I'm not sure what to do..."}

    def _create_prompt(self, context: Dict) -> str:
        return f"""
Current situation:
Location: {context['current_room']}
Available objects: {', '.join(context['available_objects'])}
Available directions: {', '.join(context['available_directions'])}

Needs Status:
{self._format_needs_status(context['needs'], context['need_status'])}

Urgent needs: {', '.join(context['urgent_needs'])}

Recent actions:
{self._format_history(context['recent_actions'])}

Recent memories:
{self._format_memories(context['recent_memories'])}

Important memories:
{self._format_memories(context['important_memories'])}

Emotional state:
{self._format_emotional_state(context['emotional_state'])}

Make a decision about what to do next. Consider:
1. Most urgent needs and their status
2. Available objects and their effects
3. Previous actions and memories
4. Current location and available movements
5. Emotional state and context

Respond with JSON in this format:
{{
    "action": "move|use|idle",
    "target": "<direction_name|object_name|null>",
    "thought": "<detailed_reasoning_for_decision>"
}}
"""

    def _format_needs_status(self, needs: Dict, status: Dict) -> str:
        return "\n".join([f"- {need}: {value:.1f} ({status[need]})" for need, value in needs.items()])

    def _format_memories(self, memories: List) -> str:
        return "\n".join([f"- {memory}" for memory in memories])

    def _format_emotional_state(self, emotional_state: Dict) -> str:
        return "\n".join([f"- {emotion}: {value:.2f}" for emotion, value in emotional_state.items()])

    def _format_history(self, history: List) -> str:
        return "\n".join([f"- {action}" for action in history[-5:]])  # Last 5 actions

    def handle_phone_call(self, context: Dict) -> str:
        prompt = self._create_phone_call_prompt(context)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-0613",
                messages=[
                    {"role": "system", "content": "You are a Sim character having a phone conversation. Respond naturally and emotionally, considering your current needs and emotional state."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in phone conversation: {e}")
            return "I'm sorry, I'm having trouble with the connection..."

    def _create_phone_call_prompt(self, context: Dict) -> str:
        return f"""
You are having a phone conversation. Here's your current state:
Location: {context['current_room']}
Emotional state: {context['emotional_state']}
Recent experiences: {context['recent_memories']}

The person on the phone says: "{context['user_message']}"

Respond naturally to this message, considering your current emotional state and needs.
"""
