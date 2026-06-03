# memory/praison_memory.py
# Praison AI Memory System
# Remembers past GR documents so system learns over time

import json
import os
import datetime

class PraisonMemory:
    """
    Long-term and episodic memory across agents
    Like a notebook that remembers every document ever processed
    """

    def __init__(self, memory_file="memory/memory.json"):
        self.memory_file = memory_file
        self.episodic    = []  # remembers what happened this session
        self.long_term   = self._load_memory()

    def _load_memory(self):
        """Load existing memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_memory(self):
        """Save memory to file"""
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w") as f:
            json.dump(self.long_term, f, indent=2)

    def store_gr_interpretation(self, source, obligations,
                                 deadlines, authorities):
        """Save a GR interpretation to long-term memory"""
        entry = {
            "timestamp":   datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
            "source":      str(source),
            "obligations": obligations,
            "deadlines":   deadlines,
            "authorities": authorities
        }
        self.long_term.append(entry)
        self._save_memory()
        self.log_episode("memory", f"Stored GR: {str(source)[:50]}")
        print(f"  [Memory] Saved to long-term memory "
              f"(total: {len(self.long_term)} GRs)")

    def get_similar_gr(self, subject):
        """Check if we have seen a similar GR before"""
        subject_lower = subject.lower()
        for entry in self.long_term:
            for obligation in entry.get("obligations", []):
                if any(word in obligation.lower()
                       for word in subject_lower.split()
                       if len(word) > 4):
                    return entry
        return None

    def log_episode(self, agent, action):
        """Log what happened in this session"""
        self.episodic.append({
            "time":   datetime.datetime.now().strftime("%H:%M:%S"),
            "agent":  agent,
            "action": action
        })

    def get_few_shot_examples(self):
        """
        Few-shot policy adaptation:
        Returns examples from memory to help agents
        write better drafts
        """
        if not self.long_term:
            return ""

        examples = []
        for entry in self.long_term[-3:]:  # last 3 GRs
            if entry.get("obligations"):
                examples.append(
                    f"Past GR had obligations: "
                    f"{', '.join(entry['obligations'][:2])}"
                )
        return "\n".join(examples) if examples else ""

    def summary(self):
        """Print memory summary"""
        print(f"\n  [Memory Summary]")
        print(f"  Long-term: {len(self.long_term)} GRs stored")
        print(f"  Episodic : {len(self.episodic)} actions this session")