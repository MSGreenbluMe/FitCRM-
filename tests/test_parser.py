"""Tests for EmailParser"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_parser import EmailParser, ClientProfile


class TestEmailParser:
    """Test cases for EmailParser"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = EmailParser()

    def test_parse_basic_email(self):
        """Test parsing a basic email with all required fields"""
        email = """
        Meno: Jan Novak
        Email: jan@example.com
        Vek: 30
        Pohlavie: muz
        Vaha: 80 kg
        Vyska: 180 cm
        Ciel: Chcem schudnut
        """

        profile = self.parser.parse_email(email)

        assert profile.name == "Jan Novak"
        assert profile.email == "jan@example.com"
        assert profile.age == 30
        assert profile.gender == "male"
        assert profile.weight == 80.0
        assert profile.height == 180.0
        assert "schudnut" in profile.goal.lower()

    def test_parse_female_client(self):
        """Test parsing email for female client"""
        email = """
        Meno: Maria Kovacova
        Email: maria@example.com
        Vek: 25
        Pohlavie: zena
        Vaha: 65 kg
        Vyska: 168 cm
        Ciel: Spevnit postavu
        """

        profile = self.parser.parse_email(email)

        assert profile.name == "Maria Kovacova"
        assert profile.gender == "female"
        assert profile.weight == 65.0

    def test_parse_with_optional_fields(self):
        """Test parsing email with optional fields"""
        email = """
        Meno: Peter Horvath
        Email: peter@example.com
        Vek: 35
        Pohlavie: muz
        Vaha: 90 kg
        Vyska: 175 cm
        Ciel: Nabrat svaly
        Aktivita: aktivna
        Skusenosti: pokrocily
        Obmedzenia: bezlepkova dieta
        """

        profile = self.parser.parse_email(email)

        assert profile.activity_level == "active"
        assert profile.experience_level == "intermediate"
        assert "bezlepkova" in profile.dietary_restrictions[0].lower()

    def test_parse_missing_required_field_raises_error(self):
        """Test that missing required fields raise ValueError"""
        email = """
        Meno: Jan Novak
        Email: jan@example.com
        """

        with pytest.raises(ValueError):
            self.parser.parse_email(email)

    def test_parse_decimal_weight(self):
        """Test parsing decimal weight values"""
        email = """
        Meno: Test User
        Email: test@example.com
        Vek: 30
        Pohlavie: muz
        Vaha: 78,5 kg
        Vyska: 175 cm
        Ciel: Udrzat vahu
        """

        profile = self.parser.parse_email(email)
        assert profile.weight == 78.5

    def test_profile_to_dict(self):
        """Test ClientProfile to_dict method"""
        profile = ClientProfile(
            name="Test User",
            email="test@example.com",
            age=30,
            gender="male",
            weight=80.0,
            height=180.0,
            goal="Test goal"
        )

        data = profile.to_dict()

        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert data["age"] == 30
        assert isinstance(data["dietary_restrictions"], list)


class TestSampleEmails:
    """Test parsing sample email files"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = EmailParser()
        self.sample_dir = Path(__file__).parent / "sample_emails"

    def test_parse_client1_weight_loss(self):
        """Test parsing weight loss client email"""
        email_path = self.sample_dir / "client1_weight_loss.txt"
        if not email_path.exists():
            pytest.skip("Sample email not found")

        email = email_path.read_text(encoding="utf-8")
        profile = self.parser.parse_email(email)

        assert profile.name == "Jan Novak"
        assert profile.weight == 92.0
        assert profile.activity_level == "sedentary"
        assert profile.experience_level == "beginner"

    def test_parse_client2_muscle_gain(self):
        """Test parsing muscle gain client email"""
        email_path = self.sample_dir / "client2_muscle_gain.txt"
        if not email_path.exists():
            pytest.skip("Sample email not found")

        email = email_path.read_text(encoding="utf-8")
        profile = self.parser.parse_email(email)

        assert profile.name == "Peter Horvath"
        assert profile.weight == 72.0
        assert profile.activity_level == "active"

    def test_parse_client3_female_fitness(self):
        """Test parsing female fitness client email"""
        email_path = self.sample_dir / "client3_female_fitness.txt"
        if not email_path.exists():
            pytest.skip("Sample email not found")

        email = email_path.read_text(encoding="utf-8")
        profile = self.parser.parse_email(email)

        assert profile.name == "Lucia Kovacova"
        assert profile.gender == "female"
        assert len(profile.dietary_restrictions) > 0  # Has lactose intolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
