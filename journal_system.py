import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

class JournalSystem:
    def __init__(self, character_name: str):
        self.character_name = character_name
        self.journal_directory = f"character_files/{character_name}/journal"
        self.logger = logging.getLogger('JournalSystem')
        self.setup_directory()

    def setup_directory(self):
        """Create necessary directories for the character's journal"""
        os.makedirs(self.journal_directory, exist_ok=True)

    def write_entry(self, content: Dict) -> bool:
        """Write a new journal entry"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            entry = {
                'timestamp': timestamp,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'content': content['text'],
                'mood': content.get('mood', {}),
                'tags': content.get('tags', []),
                'related_memories': content.get('related_memories', [])
            }

            filename = f"entry_{timestamp}.json"
            file_path = os.path.join(self.journal_directory, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Created journal entry: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing journal entry: {str(e)}")
            return False

    def read_entries(self, count: int = 5) -> List[Dict]:
        """Read the most recent journal entries"""
        try:
            entries = []
            files = sorted([f for f in os.listdir(self.journal_directory) 
                          if f.startswith('entry_') and f.endswith('.json')],
                         reverse=True)
            
            for filename in files[:count]:
                file_path = os.path.join(self.journal_directory, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries.append(json.load(f))
            
            return entries
        except Exception as e:
            self.logger.error(f"Error reading journal entries: {str(e)}")
            return []

    def get_entry_by_date(self, date_str: str) -> Optional[Dict]:
        """Find an entry by date"""
        try:
            for filename in os.listdir(self.journal_directory):
                if filename.startswith('entry_') and filename.endswith('.json'):
                    file_path = os.path.join(self.journal_directory, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entry = json.load(f)
                        if date_str in entry['date']:
                            return entry
            return None
        except Exception as e:
            self.logger.error(f"Error finding journal entry: {str(e)}")
            return None

    def search_entries(self, keyword: str) -> List[Dict]:
        """Search journal entries for a keyword"""
        try:
            matching_entries = []
            for filename in os.listdir(self.journal_directory):
                if filename.startswith('entry_') and filename.endswith('.json'):
                    file_path = os.path.join(self.journal_directory, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entry = json.load(f)
                        if (keyword.lower() in entry['content'].lower() or
                            keyword.lower() in str(entry['tags']).lower()):
                            matching_entries.append(entry)
            return matching_entries
        except Exception as e:
            self.logger.error(f"Error searching journal entries: {str(e)}")
            return [] 