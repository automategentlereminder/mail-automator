import re
import random
import logging

logger = logging.getLogger(__name__)

class TemplateParser:
    @staticmethod
    def parse_spintax(text):
        """
        Recursively parses spintax {option1|option2|option3} variants.
        """
        pattern = re.compile(r'\{([^{}]*)\}')
        
        while True:
            match = pattern.search(text)
            if not match:
                break
            
            options = match.group(1).split('|')
            choice = random.choice(options)
            text = text[:match.start()] + choice + text[match.end():]
            
        return text

    @staticmethod
    def inject_variables(text, row_data):
        """
        Injects variables in the format {{CSV:ColumnName}} or {{CSV:ColumnName|Fallback}}
        from a dictionary representing a row of data.
        """
        # Find all {{CSV:VAR}} or {{CSV:VAR|Fallback}}
        pattern = re.compile(r'\{\{CSV:([^}|]+)(?:\|([^}]+))?\}\}')
        
        def replacer(match):
            column_name = match.group(1).strip()
            fallback = match.group(2)
            
            # Check if column exists in row_data
            if column_name in row_data and row_data[column_name]:
                val = str(row_data[column_name])
                if val.strip() != '' and val.lower() != 'nan':
                    return val
                    
            if fallback:
                return fallback
                
            return "" # Default empty if no fallback
            
        return pattern.sub(replacer, text)

    @staticmethod
    def render(template_text, row_data, apply_spintax=True):
        """
        Full render pipeline: Inject variables, then apply spintax.
        """
        # Option 1: Inject variables first, so spintax can be data-driven
        text = TemplateParser.inject_variables(template_text, row_data)
        
        # Option 2: Apply spintax
        if apply_spintax:
            text = TemplateParser.parse_spintax(text)
            
        return text
