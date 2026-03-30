"""Tests for is_valid_name() from sync_to_canvas.py."""

from sync_to_canvas import is_valid_name


class TestIsValidName:

    def test_two_digit_prefix(self):
        assert is_valid_name("01_Intro") is True

    def test_high_number(self):
        assert is_valid_name("99_Last") is True

    def test_single_digit_rejected(self):
        assert is_valid_name("1_Intro") is False

    def test_no_prefix(self):
        assert is_valid_name("Intro") is False

    def test_hidden_file(self):
        assert is_valid_name(".hidden") is False

    def test_three_digits_rejected(self):
        """'001_X' — after matching '00', expects '_' at pos 2 but finds '1'."""
        assert is_valid_name("001_Intro") is False

    def test_underscores_in_name(self):
        assert is_valid_name("01_My_File_Name") is True

    def test_just_prefix(self):
        assert is_valid_name("01_") is True

    def test_empty_string(self):
        assert is_valid_name("") is False

    def test_digits_no_underscore(self):
        assert is_valid_name("01Intro") is False

    def test_spaces_in_name(self):
        assert is_valid_name("02_Python Basics") is True
