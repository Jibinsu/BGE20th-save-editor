"""
Translation module for French to English variable names and descriptions.
Beyond Good & Evil was developed by Ubisoft (French company) and contains
many French variable names in the save data.
"""

from typing import Dict, Optional
import re

class FrenchTranslator:
    """Handles translation of French variable names and descriptions to English"""
    
    # Direct translations for known French terms
    DIRECT_TRANSLATIONS = {
        # Currency and economy
        'fric': 'credits',
        'argent': 'money',
        'credit': 'credits',
        'credits': 'credits',
        'f_sally_fric': 'sally_credits',
        
        # Health and stats
        'vie': 'life',
        'sante': 'health',
        'energie': 'energy',
        'force': 'strength',
        'vitesse': 'speed',
        'defense': 'defense',
        
        # Items and inventory
        'inventaire': 'inventory',
        'objet': 'object',
        'objets': 'objects',
        'item': 'item',
        'items': 'items',
        'equipement': 'equipment',
        'arme': 'weapon',
        'armes': 'weapons',
        
        # Collectibles
        'perle': 'pearl',
        'perles': 'pearls',
        'photo': 'photo',
        'photos': 'photos',
        'image': 'image',
        'images': 'images',
        
        # Characters and companions
        'compagnon': 'companion',
        'compagnons': 'companions',
        'animal': 'animal',
        'animaux': 'animals',
        'jade': 'jade',
        'pey': 'pey',
        'double_h': 'double_h',
        
        # Locations
        'hillys': 'hillys',
        'usine': 'factory',
        'ville': 'city',
        'maison': 'house',
        'laboratoire': 'laboratory',
        'labo': 'lab',
        
        # Game mechanics
        'niveau': 'level',
        'score': 'score',
        'temps': 'time',
        'duree': 'duration',
        'position': 'position',
        'coordonnee': 'coordinate',
        'coordonnees': 'coordinates',
        'sauvegarde': 'save',
        'checkpoint': 'checkpoint',
        
        # Actions and states
        'actif': 'active',
        'inactive': 'inactive',
        'complete': 'complete',
        'termine': 'finished',
        'commence': 'started',
        'disponible': 'available',
        'verrouille': 'locked',
        'deverrouille': 'unlocked',
        
        # Quantities and measurements
        'nombre': 'number',
        'quantite': 'quantity',
        'total': 'total',
        'maximum': 'maximum',
        'minimum': 'minimum',
        'valeur': 'value',
        
        # Technical terms
        'donnee': 'data',
        'donnees': 'data',
        'fichier': 'file',
        'dossier': 'folder',
        'configuration': 'configuration',
        'parametre': 'parameter',
        'parametres': 'parameters',
    }
    
    # Pattern-based translations for complex terms
    PATTERN_TRANSLATIONS = [
        # Numbers and indices
        (r'(\w+)_(\d+)', r'\1_\2'),  # Keep numbered items as-is
        
        # Prefixes
        (r'^nb_(.+)', r'count_\1'),  # nb_ = number of
        (r'^max_(.+)', r'max_\1'),   # max_ prefix
        (r'^min_(.+)', r'min_\1'),   # min_ prefix
        (r'^pos_(.+)', r'position_\1'),  # pos_ = position
        
        # Common suffixes
        (r'(.+)_actuel$', r'current_\1'),  # _actuel = current
        (r'(.+)_total$', r'total_\1'),     # _total = total
        (r'(.+)_max$', r'max_\1'),         # _max = maximum
        (r'(.+)_min$', r'min_\1'),         # _min = minimum
    ]
    
    # Descriptions for translated terms
    DESCRIPTIONS = {
        'sally_credits': 'Credits earned from Sally (main currency)',
        'credits': 'Game currency for purchasing items',
        'life': 'Player health/life points',
        'health': 'Current health status',
        'energy': 'Energy level for special abilities',
        'pearl': 'Collectible pearls (main collectible)',
        'pearls': 'Collection of pearls found',
        'photo': 'Photograph taken in-game',
        'photos': 'Collection of photographs',
        'companion': 'AI companion character',
        'jade': 'Main character Jade',
        'pey': 'Companion character Pey\'j',
        'hillys': 'Planet Hillys (game world)',
        'inventory': 'Player inventory system',
        'equipment': 'Equipped items and gear',
        'level': 'Game progress level',
        'position': 'Character position coordinates',
        'active': 'Currently active/enabled',
        'unlocked': 'Available for use',
        'locked': 'Not yet available',
        'count': 'Number of items',
        'total': 'Total amount/quantity',
    }
    
    def __init__(self):
        """Initialize the translator"""
        self.translation_cache = {}
    
    def translate_key(self, key: str) -> str:
        """
        Translate a French key to English.
        
        Args:
            key: The French key to translate
            
        Returns:
            English translation of the key
        """
        if key in self.translation_cache:
            return self.translation_cache[key]
        
        original_key = key
        key_lower = key.lower()
        
        # Check direct translations first
        if key_lower in self.DIRECT_TRANSLATIONS:
            translated = self.DIRECT_TRANSLATIONS[key_lower]
            self.translation_cache[original_key] = translated
            return translated
        
        # Check pattern-based translations
        for pattern, replacement in self.PATTERN_TRANSLATIONS:
            if re.match(pattern, key_lower):
                translated = re.sub(pattern, replacement, key_lower)
                # Check if any part needs direct translation
                parts = translated.split('_')
                translated_parts = []
                for part in parts:
                    if part in self.DIRECT_TRANSLATIONS:
                        translated_parts.append(self.DIRECT_TRANSLATIONS[part])
                    else:
                        translated_parts.append(part)
                translated = '_'.join(translated_parts)
                self.translation_cache[original_key] = translated
                return translated
        
        # If no translation found, return original
        self.translation_cache[original_key] = key
        return key
    
    def get_description(self, key: str) -> Optional[str]:
        """
        Get a description for a translated key.
        
        Args:
            key: The key to get description for
            
        Returns:
            Description if available, None otherwise
        """
        translated_key = self.translate_key(key)
        return self.DESCRIPTIONS.get(translated_key.lower())
    
    def translate_value_description(self, key: str, value: any) -> str:
        """
        Create a descriptive translation for a key-value pair.
        
        Args:
            key: The key name
            value: The value
            
        Returns:
            Descriptive string combining translation and description
        """
        translated_key = self.translate_key(key)
        description = self.get_description(key)
        
        result = f"{translated_key}"
        if translated_key != key:
            result += f" (was: {key})"
        
        if description:
            result += f" - {description}"
        
        return result
    
    def get_search_terms(self, key: str) -> list:
        """
        Get all possible search terms for a key (original + translated).
        
        Args:
            key: The key to get search terms for
            
        Returns:
            List of search terms
        """
        terms = [key.lower()]
        translated = self.translate_key(key)
        if translated != key:
            terms.append(translated.lower())
        
        # Add partial matches
        for part in key.split('_'):
            if part.lower() not in terms:
                terms.append(part.lower())
        
        for part in translated.split('_'):
            if part.lower() not in terms:
                terms.append(part.lower())
        
        return terms

# Global translator instance
translator = FrenchTranslator()