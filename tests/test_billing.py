"""Tests for cbsserverbilling.billing"""

import datetime

from cbsserverbilling import billing

MOCK_PI_FORM = "tests/resources/mock_pi_form.xlsx"
MOCK_USER_FORM = "tests/resources/mock_user_form.xlsx"


def test_user_price_by_index():
    """Test that `user_price_by_index` produces the correct prices."""
    assert billing.user_price_by_index(0) == billing.FIRST_POWERUSER_PRICE
    assert billing.user_price_by_index(1) == billing.ADDITIONAL_POWERUSER_PRICE


def test_load_pi_df():
    """Test that `load_pi_df` properly loads the PI form data."""
    pi_df = billing.load_pi_df(MOCK_PI_FORM)
    for actual, expected in zip(pi_df.columns, ["timestamp",
                                                "email",
                                                "first_name",
                                                "last_name",
                                                "storage",
                                                "pi_is_power_user",
                                                "speed_code"]):
        assert actual == expected
    assert len(pi_df.index) == 6


def test_load_user_df():
    """Test that `load_user_df` properly loads the user form data."""
    user_df = billing.load_user_df(MOCK_USER_FORM)
    for actual, expected in zip(user_df.columns, ["timestamp",
                                                  "email",
                                                  "first_name",
                                                  "last_name",
                                                  "pi_last_name",
                                                  "power_user"]):
        assert actual == expected
    assert len(user_df.index) == 4


def test_preprocess_forms():
    """Test that `preprocess_forms` correctly assembles the data"""
    pi_df, user_df = billing.preprocess_forms(MOCK_PI_FORM, MOCK_USER_FORM)
    assert len(pi_df.index) == 6
    assert len(user_df.index) == 10
    assert user_df.loc[4, "last_name"] == "Apple"


def test_assemble_bill():
    """Test that `assemble_bill` works properly for all PIs."""
    pi_df, user_df = billing.preprocess_forms(MOCK_PI_FORM, MOCK_USER_FORM)
    pi_lastname = "Apple"
    quarter_end = datetime.datetime(2020, 12, 31)

    for pi_lastname, expected_total in zip(
            [
                "Apple",
                "Banana",
                "Cherry",
                "Durian",
                "Ice Cream",
                "Jackfruit"],
            [250, 125+250, 62.5+250, 12.5+375, 25, 37.5+250]):
        bill = billing.assemble_bill(pi_df, user_df, pi_lastname, quarter_end)

        assert bill.calculate_total() == expected_total


def test_generate_pi_bill(capsys, tmp_path):
    """Test that `generate_pi_bill` populates a bill correctly."""
    billing.generate_pi_bill(MOCK_PI_FORM,
                             MOCK_USER_FORM,
                             "Apple",
                             "2020-12-31")

    bill = capsys.readouterr().out
    expected_bill = "\n".join([
        "Billing report for Apple",
        "Storage",
        "Start: 2019-12-10, Size: 20 TB, Annual price per TB: $50.00, "
        + "Quarterly Price: $250.00",
        "Speed code: AAAA, Subtotal: $250.00",
        "Power Users",
        "Speed code: AAAA, Subtotal: $0.00",
        "Total: $250.00\n"])

    assert bill == expected_bill

    billing.generate_pi_bill(MOCK_PI_FORM,
                             MOCK_USER_FORM,
                             "Banana",
                             "2020-12-31",
                             out_file=tmp_path / "test.txt")

    expected_bill = "\n".join([
        "Billing report for Banana",
        "Storage",
        "Start: 2019-12-10, Size: 10 TB, Annual price per TB: $50.00, "
        + "Quarterly Price: $125.00",
        "Speed code: BBBB, Subtotal: $125.00",
        "Power Users",
        "Name: Fruit, Start: 2020-01-27, Annual price: $1000.00, "
        + "Quarterly price: $250.00",
        "Speed code: BBBB, Subtotal: $250.00",
        "Total: $375.00\n"])

    with open(tmp_path / "test.txt", "r") as report_file:
        assert report_file.read() == expected_bill
