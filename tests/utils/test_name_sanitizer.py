"""Tests for agent name sanitization."""

from autobox.utils.name_sanitizer import create_name_mapping, sanitize_agent_name


class TestNameSanitizer:
    """Test agent name sanitization."""

    def test_sanitize_nordic_characters(self):
        """Test sanitization of Nordic characters."""
        assert sanitize_agent_name("ANNA BERGSTRÖM") == "ANNA BERGSTROM"
        assert sanitize_agent_name("Erik Söderberg") == "Erik Soderberg"
        assert sanitize_agent_name("Åsa Lindqvist") == "Asa Lindqvist"
        assert sanitize_agent_name("Bjørn Hansen") == "Bjorn Hansen"
        assert sanitize_agent_name("Pär Östlund") == "Par Ostlund"

    def test_sanitize_european_characters(self):
        """Test sanitization of European characters."""
        assert sanitize_agent_name("François Müller") == "Francois Muller"
        assert sanitize_agent_name("José García") == "Jose Garcia"
        assert sanitize_agent_name("Jürgen Straße") == "Jurgen Strasse"
        assert sanitize_agent_name("Niño de la Cruz") == "Nino de la Cruz"
        assert sanitize_agent_name("Ça va bien") == "Ca va bien"

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
        assert sanitize_agent_name("Alice Smith Jr.") == "Alice Smith Jr."
        assert sanitize_agent_name("Agent_123") == "Agent_123"

    def test_clean_whitespace(self):
        """Test whitespace cleaning."""
        assert sanitize_agent_name("  John  Smith  ") == "John Smith"
        assert sanitize_agent_name("Mary\t\tJohnson") == "Mary Johnson"
        assert sanitize_agent_name("Bob   Anderson") == "Bob Anderson"

    def test_empty_and_invalid_names(self):
        """Test handling of empty and invalid names."""
        assert sanitize_agent_name("") == ""
        assert sanitize_agent_name("   ") == ""
        assert sanitize_agent_name("@#$%") == ""

    def test_create_name_mapping(self):
        """Test creation of name mappings."""
        names = ["ANNA BERGSTRÖM", "Erik Söderberg", "John Smith", "Jane Doe"]

        mapping = create_name_mapping(names)

        assert mapping["ANNA BERGSTRÖM"] == "ANNA BERGSTROM"
        assert mapping["Erik Söderberg"] == "Erik Soderberg"
        assert mapping["John Smith"] == "John Smith"
        assert mapping["Jane Doe"] == "Jane Doe"

    def test_handle_name_collisions(self):
        """Test handling of name collisions after sanitization."""
        names = [
            "Åsa Smith",
            "Asa Smith",  # Already "Asa Smith" - collision!
            "ÅSA SMITH",
        ]

        mapping = create_name_mapping(names)

        assert mapping["Åsa Smith"] == "Asa Smith"
        assert mapping["Asa Smith"] == "Asa Smith_2"
        assert mapping["ÅSA SMITH"] == "ASA SMITH"
