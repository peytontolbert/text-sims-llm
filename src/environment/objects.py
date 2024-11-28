import json
from typing import Dict, Optional
from pathlib import Path
from src.utils.models import GameObject, ActivityInfo
from src.utils.constants import ObjectType, ActivityType

class ObjectManager:
    def __init__(self):
        self.house_items: Dict[str, GameObject] = {}
        self.store_items: Dict[str, Dict[str, GameObject]] = {}
        self.load_items()

    def load_items(self):
        # Load house items
        house_items_path = Path(__file__).parent / "house_items.json"
        with open(house_items_path, 'r') as f:
            house_data = json.load(f)
            for item_id, item_data in house_data.items():
                activity_info = None
                if 'activity_info' in item_data:
                    activity_info = ActivityInfo(
                        type=ActivityType[item_data['activity_info']['type']],
                        duration=item_data['activity_info']['duration'],
                        need_changes=item_data['activity_info']['need_changes']
                    )
                    
                self.house_items[item_id] = GameObject(
                    type=ObjectType[item_data['type']],
                    actions=item_data['actions'],
                    need_effects=item_data['need_effects'],
                    description=item_data['description'],
                    activity_info=activity_info
                )

        # Load store items
        store_items_path = Path(__file__).parent / "store_items.json"
        with open(store_items_path, 'r') as f:
            store_data = json.load(f)
            for category, items in store_data.items():
                self.store_items[category] = {}
                for item_id, item_data in items.items():
                    self.store_items[category][item_id] = GameObject(
                        type=ObjectType[item_data['type']],
                        actions=item_data['actions'],
                        need_effects=item_data['need_effects'],
                        description=item_data['description']
                    )

    def get_house_item(self, item_id: str) -> Optional[GameObject]:
        return self.house_items.get(item_id)

    def get_store_item(self, category: str, item_id: str) -> Optional[GameObject]:
        if category in self.store_items:
            return self.store_items[category].get(item_id)
        return None

    def get_store_categories(self) -> list[str]:
        return list(self.store_items.keys())

    def get_items_in_category(self, category: str) -> Dict[str, GameObject]:
        return self.store_items.get(category, {})
