"""Tests for agent name sanitization."""

from autobox.utils.name_sanitizer import create_name_mapping, sanitize_agent_name


class TestNameSanitizer:
    """Test agent name sanitization."""

    def test_sanitize_nordic_characters(self):
        """Test sanitization of Nordic characters."""
        assert sanitize_agent_name("ANNA BERGSTRÖM") == "ANNA_BERGSTROM"
        assert sanitize_agent_name("Erik Söderberg") == "Erik_Soderberg"
        assert sanitize_agent_name("Åsa Lindqvist") == "Asa_Lindqvist"
        assert sanitize_agent_name("Bjørn Hansen") == "Bjorn_Hansen"
        assert sanitize_agent_name("Pär Östlund") == "Par_Ostlund"

    def test_sanitize_european_characters(self):
        """Test sanitization of European characters."""
        assert sanitize_agent_name("François Müller") == "Francois_Muller"
        assert sanitize_agent_name("José García") == "Jose_Garcia"
        assert sanitize_agent_name("Jürgen Straße") == "Jurgen_Strasse"
        assert sanitize_agent_name("Niño de la Cruz") == "Nino_de_la_Cruz"
        assert sanitize_agent_name("Ça va bien") == "Ca_va_bien"

    def test_sanitize_special_characters(self):
        """Test removal of special characters."""
        assert sanitize_agent_name("John@Smith") == "JohnSmith"
        assert sanitize_agent_name("Mary#Johnson") == "MaryJohnson"
        assert sanitize_agent_name("Bob$Anderson") == "BobAnderson"
        assert sanitize_agent_name("Alice&Bob") == "AliceBob"
        assert sanitize_agent_name("Tom*Jones") == "TomJones"

    def test_preserve_allowed_characters(self):
        """Test that allowed characters are preserved."""
        assert sanitize_agent_name("John_Smith") == "John_Smith"
        assert sanitize_agent_name("Mary-Johnson") == "Mary-Johnson"
        assert sanitize_agent_name("Bob.Anderson") == "Bob.Anderson"
        assert sanitize_agent_name("Alice Smith Jr.") == "Alice_Smith_Jr."
        assert sanitize_agent_name("Agent_123") == "Agent_123"

    def test_clean_whitespace(self):
        """Test whitespace cleaning."""
        assert sanitize_agent_name("  John  Smith  ") == "John_Smith"
        assert sanitize_agent_name("Mary		Johnson") == "Mary_Johnson"
        assert sanitize_agent_name("Bob   Anderson") == "Bob_Anderson"

    def test_empty_and_invalid_names(self):
        """Test handling of empty and invalid names."""
        assert sanitize_agent_name("") == ""
        assert sanitize_agent_name("   ") == ""
        assert sanitize_agent_name("@#$%") == ""

    def test_create_name_mapping(self):
        """Test creation of name mappings."""
        names = ["ANNA BERGSTRÖM", "Erik Söderberg", "John Smith", "Jane Doe"]

        mapping = create_name_mapping(names)

        assert mapping["ANNA BERGSTRÖM"] == "ANNA_BERGSTROM"
        assert mapping["Erik Söderberg"] == "Erik_Soderberg"
        assert mapping["John Smith"] == "John_Smith"
        assert mapping["Jane Doe"] == "Jane_Doe"

    def test_handle_name_collisions(self):
        """Test handling of name collisions after sanitization."""
        names = [
            "Åsa Smith",
            "Asa Smith",  # Already "Asa Smith" - collision!
            "ÅSA SMITH",
        ]

        mapping = create_name_mapping(names)

        assert mapping["Åsa Smith"] == "Asa_Smith"
        assert mapping["Asa Smith"] == "Asa_Smith_2"
        assert mapping["ÅSA SMITH"] == "ASA_SMITH"
