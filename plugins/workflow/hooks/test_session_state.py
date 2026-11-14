import session_state


def test_describe_lists_background_runs_and_marks_own_chat():
    sessions = [
        {"kind": "interactive", "name": "Monitor", "sessionId": "me", "status": "busy",
         "startedAt": 1_794_689_826_132},
        {"kind": "background", "id": "e0778c0e", "name": "selfdrive-b", "status": "busy",
         "startedAt": 1_794_689_870_000},
        {"kind": "background", "id": "0102d884", "name": "selfdrive-a", "status": "idle",
         "startedAt": 1_794_686_500_543},
    ]
    line = session_state.describe(sessions, "me")
    assert line.index("selfdrive-a") < line.index("selfdrive-b")  # oldest run first
    assert "selfdrive-a (idle, since " in line
    assert "Monitor (you) (busy)" in line


def test_describe_with_no_sessions():
    assert session_state.describe([], "me") == "background sessions: none · interactive chats: none"


def test_describe_tolerates_missing_fields():
    line = session_state.describe([{"kind": "background"}], "me")
    assert "? (?, since ?)" in line
