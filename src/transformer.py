import re
import random
import logging
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag

logger = logging.getLogger(__name__)

class CompLinguisticsTransformer:
    """
    A class for transforming ordinary text into computational linguistics style.
    """
    
    def __init__(self, custom_terminology=None):
        """
        Initialize the transformer with default or custom terminology.
        
        Args:
            custom_terminology (dict, optional): Custom terminology mapping.
        """
        # Default technical term mappings
        self.term_mapping = {
            # Verbs
            "organize": "implement hierarchical organization of",
            "look": "perform corpus traversal across",
            "find": "identify",
            "check": "verify lexical and syntactic correctness of",
            "fix": "resolve anomalous patterns in",
            "use": "leverage",
            "start": "initiate",
            "continue": "proceed with subsequent modules in",
            "create": "generate structured artifacts for",
            "update": "refactor",
            "work": "execute operations on",
            "focus": "prioritize implementation of",
            "make": "construct",
            "give": "provide contextual metadata for",
            
            # Nouns
            "code": "codebase",
            "files": "syntax tree components",
            "problems": "anomalous patterns",
            "errors": "syntactic inconsistencies",
            "bugs": "implementation defects",
            "project": "development corpus",
            "steps": "sequential components",
            "parts": "modular elements",
            "document": "knowledge transfer schema",
            "list": "enumerated entities",
            "info": "metadata",
            "folders": "directory hierarchy",
            "structure": "architectural schema",
            
            # Adjectives
            "first": "initial",
            "important": "critical",
            "main": "primary",
            "clear": "explicit",
            "good": "optimal",
            "bad": "suboptimal",
            "new": "subsequent",
            
            # Phrases
            "look for": "identify instances of",
            "go through": "traverse the lexical structure of",
            "set up": "initialize the configuration parameters for",
            "find out": "determine through systematic analysis",
            "write down": "document in structured format",
            "keep track of": "maintain referential integrity for",
            "make sure": "ensure syntactic validity of",
            "pay attention to": "maintain semantic focus on",
            "next steps": "subsequent procedural elements",
        }
        
        # Update with custom terminology if provided
        if custom_terminology and isinstance(custom_terminology, dict):
            self.term_mapping.update(custom_terminology)
        
        # Technical domain nouns to insert for added complexity
        self.technical_nouns = [
            "abstract syntax tree",
            "lexical analysis",
            "syntactic patterns",
            "referential integrity",
            "modular components", 
            "dependency hierarchy",
            "implementation pipeline",
            "code corpus",
            "semantic structure",
            "lexical tokens",
            "syntactic schema",
            "architectural paradigm",
            "module granularity",
            "dependency graph",
            "namespace resolution",
        ]
        
        # Technical modifiers to enhance terminology
        self.technical_modifiers = [
            "hierarchical",
            "sequential",
            "systematic",
            "structured",
            "modular",
            "granular",
            "lexical",
            "syntactic",
            "semantic",
            "architectural",
            "paradigmatic",
            "comprehensive",
            "discrete",
            "optimal",
            "explicit",
        ]
        
        # Sentence structure transformations
        self.structure_patterns = [
            # Command forms
            (r"(?i)^(check|look at|find|fix|update)(.*)", r"Systematically \1\2"),
            (r"(?i)^(use|create|make|give)(.*)", r"Implement methodology to \1\2"),
            
            # Question forms
            (r"(?i)^(how (do|can|should) (i|we))(.*)\?", r"What is the optimal approach to\4?"),
            (r"(?i)^(can you|could you|would you)(.*)\?", r"Is it feasible to\2?"),
            
            # Statement forms
            (r"(?i)^(i want|we need|please)(.*)", r"It is necessary to\2"),
            (r"(?i)^(i think|i believe)(.*)", r"Analysis indicates\2"),
        ]
        
        # Formal sentence starters to add formality
        self.formal_starters = [
            "Execute sequential development to",
            "Implement a systematic approach to",
            "Perform hierarchical analysis to",
            "Maintain strict adherence to",
            "Prioritize implementation of",
            "Generate structured documentation for",
            "Establish referential integrity through",
            "Systematically traverse",
            "Verify syntactic correctness of",
        ]
    
    def _replace_terms(self, text, intensity=0.8):
        """
        Replace common terms with technical equivalents.
        
        Args:
            text (str): Text to transform
            intensity (float): Transformation intensity (0.0-1.0)
            
        Returns:
            str: Text with replaced terms
        """
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)
        
        new_tokens = []
        i = 0
        while i < len(tokens):
            # Check for multi-word phrases first
            phrase_found = False
            for j in range(min(4, len(tokens) - i), 0, -1):
                phrase = ' '.join(tokens[i:i+j]).lower()
                if phrase in self.term_mapping:
                    # Apply replacement based on intensity
                    if random.random() < intensity:
                        new_tokens.append(self.term_mapping[phrase])
                    else:
                        new_tokens.extend(tokens[i:i+j])
                    i += j
                    phrase_found = True
                    break
            
            if not phrase_found:
                # Check single word
                word = tokens[i].lower()
                if word in self.term_mapping and random.random() < intensity:
                    new_tokens.append(self.term_mapping[word])
                else:
                    new_tokens.append(tokens[i])
                i += 1
        
        return ' '.join(new_tokens)
    
    def _restructure_sentence(self, sentence, intensity=0.8):
        """
        Apply structural transformations to the sentence.
        
        Args:
            sentence (str): Sentence to transform
            intensity (float): Transformation intensity (0.0-1.0)
            
        Returns:
            str: Transformed sentence
        """
        # Only apply restructuring based on intensity
        if random.random() > intensity:
            return sentence
            
        for pattern, replacement in self.structure_patterns:
            if re.match(pattern, sentence):
                return re.sub(pattern, replacement, sentence)
        
        # If no pattern matches and sentence is short, add a formal starter
        if len(sentence.split()) < 8 and random.random() < intensity:
            # Ensure we don't start with "I" or other personal pronouns
            if not re.match(r"(?i)^(i|we|you|they|he|she|it)\b", sentence):
                return random.choice(self.formal_starters) + " " + sentence
        
        return sentence
    
    def _add_technical_embellishments(self, text, intensity=0.8, advanced=False):
        """
        Add technical terms and modifiers to enhance the style.
        
        Args:
            text (str): Text to embellish
            intensity (float): Transformation intensity (0.0-1.0)
            advanced (bool): Whether to use advanced transformations
            
        Returns:
            str: Embellished text
        """
        if random.random() > intensity:
            return text
            
        sentences = sent_tokenize(text)
        embellished = []
        
        for sentence in sentences:
            # Add technical nouns (roughly 30% chance per sentence)
            if random.random() < 0.3 * intensity:
                tech_noun = random.choice(self.technical_nouns)
                # Find suitable places to insert the noun
                if "the" in sentence.lower() and random.random() < 0.7:
                    sentence = re.sub(r"(?i)\bthe\b", f"the {tech_noun}", sentence, count=1)
                else:
                    words = sentence.split()
                    if len(words) > 3:
                        insert_pos = random.randint(1, len(words) - 2)
                        words.insert(insert_pos, f"within the context of {tech_noun}")
                        sentence = ' '.join(words)
            
            # Add technical modifiers (roughly 40% chance per sentence)
            if random.random() < 0.4 * intensity:
                tech_modifier = random.choice(self.technical_modifiers)
                # Find nouns to modify
                words = word_tokenize(sentence)
                tagged = pos_tag(words)
                for i, (word, tag) in enumerate(tagged):
                    if tag.startswith('NN') and i > 0 and random.random() < 0.7:
                        words[i] = f"{tech_modifier} {word}"
                        sentence = ' '.join(words)
                        break
                        
            # Advanced transformations (paid tiers only)
            if advanced and random.random() < 0.3 * intensity:
                # Nominalization: convert verbs to noun phrases
                words = word_tokenize(sentence)
                tagged = pos_tag(words)
                for i, (word, tag) in enumerate(tagged):
                    if tag.startswith('VB') and i > 0 and i < len(words) - 1:
                        # Convert verb to noun form if possible
                        noun_forms = {
                            'implement': 'implementation',
                            'develop': 'development',
                            'execute': 'execution',
                            'analyze': 'analysis',
                            'process': 'processing',
                            'transform': 'transformation',
                            'generate': 'generation',
                            'organize': 'organization',
                            'structure': 'structuring',
                            'refactor': 'refactoring'
                        }
                        if word.lower() in noun_forms and random.random() < 0.6:
                            words[i] = f"the {noun_forms[word.lower()]} of"
                            sentence = ' '.join(words)
                            break
            
            embellished.append(sentence)
        
        return ' '.join(embellished)
    
    def _formalize_ending(self, text, intensity=0.8):
        """
        Add a formal ending to longer text when appropriate.
        
        Args:
            text (str): Text to formalize
            intensity (float): Transformation intensity (0.0-1.0)
            
        Returns:
            str: Text with formal ending
        """
        if len(text) < 100 or random.random() > intensity:
            return text
            
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return text
            
        formal_endings = [
            " This approach ensures optimal implementation of the architectural schema.",
            " Maintaining referential integrity throughout this process is essential.",
            " This methodology aligns with established computational paradigms.",
            " Strict adherence to this framework will facilitate efficient development.",
        ]
        
        # Only add ending if the text doesn't already end with punctuation
        last_sentence = sentences[-1]
        if not last_sentence.rstrip().endswith(('.', '!', '?')):
            last_sentence += "."
            
        if random.random() < intensity:
            sentences[-1] = last_sentence + random.choice(formal_endings)
            
        return ' '.join(sentences)
    
    def transform(self, text, intensity=0.7, advanced=False):
        """
        Transform ordinary text into computational linguistics style.
        
        Args:
            text (str): Original text to transform
            intensity (float): Transformation intensity (0.0-1.0)
                0: minimal transformation
                1: maximum technical terminology
            advanced (bool): Whether to use advanced transformations
                
        Returns:
            tuple: (transformed_text, stats_dict)
        """
        # Validate inputs
        if not text or not isinstance(text, str):
            return "Invalid input text.", {"words": 0, "chars": 0}
        
        intensity = max(0.0, min(1.0, float(intensity)))
        
        # Track original word and character counts
        original_words = len(re.findall(r'\b\w+\b', text))
        original_chars = len(text)
        
        # Apply transformations
        sentences = sent_tokenize(text)
        transformed_sentences = []
        
        for sentence in sentences:
            # Step 1: Basic term replacement
            s = self._replace_terms(sentence, intensity)
            
            # Step 2: Sentence restructuring
            s = self._restructure_sentence(s, intensity)
            
            # Step 3: Add technical embellishments
            s = self._add_technical_embellishments(s, intensity, advanced)
            
            transformed_sentences.append(s)
        
        result = ' '.join(transformed_sentences)
        
        # Step 4: Add formal ending if appropriate
        result = self._formalize_ending(result, intensity)
        
        # Calculate statistics
        transformed_words = len(re.findall(r'\b\w+\b', result))
        transformed_chars = len(result)
        
        stats = {
            "words": transformed_words - original_words,
            "chars": transformed_chars - original_chars
        }
        
        return result, stats
