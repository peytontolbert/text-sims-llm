# File: llm_interface.py
import openai
import os
from typing import Dict, List
import json
from dotenv import load_dotenv
from datetime import datetime
import time
from knowledge_system import KnowledgeSystem

load_dotenv()

class LLMDecisionMaker:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=self.api_key)
        self.conversation_history = []
        self.knowledge_system = KnowledgeSystem()

    def make_decision(self, context: Dict) -> Dict:
        knowledge_context = self._get_relevant_knowledge(context)
        enhanced_prompt = self._create_enhanced_prompt(context, knowledge_context)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-0613",
                messages=[
                    {"role": "system", "content": "You are an AI controlling a Sim character in a simulation game. Make decisions based on the character's needs, surroundings, previous actions, and accumulated knowledge."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            decision = json.loads(response.choices[0].message.content)
            
            # Store the decision as episodic memory
            self.knowledge_system.add_episodic_memory(
                f"Decided to {decision['action']} {decision['target']} because {decision['thought']}",
                emotions=context.get('emotional_state', {})
            )
            
            # Log the full context and response
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'prompt': enhanced_prompt,
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

    def _get_relevant_knowledge(self, context: Dict) -> Dict:
        """Query knowledge system for relevant information"""
        query = f"Current room: {context['current_room']}. Needs: {context['urgent_needs']}. Recent actions: {context['recent_actions'][-1] if context['recent_actions'] else 'none'}"
        return self.knowledge_system.query_knowledge(query)

    def _create_enhanced_prompt(self, context: Dict, knowledge: Dict) -> str:
        prompt = self._create_prompt(context)  # Original prompt creation
        
        # Add knowledge context
        knowledge_section = """
Relevant Knowledge:
Semantic (Facts & Concepts):
{}

Recent Experiences:
{}

Recurring Patterns:
{}
""".format(
            "\n".join(f"- {m['content']}" for m in knowledge['semantic'][:3]),
            "\n".join(f"- {m['content']}" for m in knowledge['episodic'][:3]),
            "\n".join(f"- {m['content']}" for m in knowledge['periodic'][:3])
        )
        
        return prompt + "\n" + knowledge_section

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

    def generate_code(self, context: dict) -> dict:
        """Generate code based on the given context"""
        prompt = f"""
        As an AI programmer, create a Python program based on the following context:
        Task: {context['prompt']}
        Previous files: {context['previous_files']}
        
        Respond with a JSON object containing:
        1. A suitable filename
        2. A brief description of the program
        3. The complete Python code
        
        The code should be:
        - Self-contained and runnable
        - Safe and without system-level operations
        - Well-commented and clear
        - Appropriate for the character's current context
        """
        
        response = self._get_llm_response(prompt)
        try:
            # Process and validate the response
            # Ensure it contains required fields and safe code
            return response
        except Exception as e:
            self.logger.error(f"Error in code generation: {str(e)}")
            return None

    def generate_journal_entry(self, context: dict) -> dict:
        """Generate a journal entry based on the given context"""
        prompt = f"""
        As an AI character writing in their journal, create an entry based on:
        Emotional state: {context['emotional_state']}
        Recent experiences: {context['recent_memories']}
        Current needs: {context['needs']}
        Location: {context['current_room']}

        Write a personal and reflective journal entry that:
        1. Expresses thoughts and feelings
        2. Reflects on recent experiences
        3. Considers current state and needs
        4. Sets goals or intentions

        Respond with a JSON object containing:
        1. The journal entry content
        2. Relevant tags for the entry
        """
        
        response = self._get_llm_response(prompt)
        try:
            # Process and validate the response
            return {
                "content": response.get("content", ""),
                "tags": response.get("tags", [])
            }
        except Exception as e:
            self.logger.error(f"Error in journal generation: {str(e)}")
            return {"content": "Failed to generate journal entry", "tags": []}
