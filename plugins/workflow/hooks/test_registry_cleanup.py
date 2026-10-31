from registry_cleanup import drop_rows

INBOX = (
    "| Chat | Session | Role |\n"
    "|---|---|---|\n"
    "| agent-1 | `4fa1e0` | lead |\n"
    "| agent-2 | `29d77b` | talk |\n"
    "Not a table row 29d77b\n"
)


def test_drops_only_the_matching_row():
    out = drop_rows(INBOX, "29d77b")
    assert "agent-2" not in out
    assert "agent-1" in out and "Not a table row 29d77b" in out


def test_no_match_changes_nothing():
    assert drop_rows(INBOX, "ffffff") == INBOX
