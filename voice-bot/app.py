"""EU CivicConnect Voice Bot — Telnyx TeXML, Flask on port 8200."""
import logging, os, sys

sys.path.insert(0, "/app/shared")
from consultations import CONSULTATIONS, EU_RESULT
from database import init_db, record_vote, has_voted, has_voted_all, get_vote_counts

from flask import Flask, request, Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
CONSULTATION_IDS = list(CONSULTATIONS.keys())
CONSULT_LIST = list(CONSULTATIONS.values())

# Init DB at import time so gunicorn workers pick it up
init_db()


def _texml(*lines: str) -> Response:
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n' + "\n".join(lines) + "\n</Response>"
    return Response(body, mimetype="application/xml")


def _say(text: str, voice: str = "en-US-Neural2-F") -> str:
    return f'  <Say voice="{voice}">{text}</Say>'


def _gather(action: str, num_digits: int = 1, timeout: int = 8) -> str:
    return f'  <Gather action="{action}" method="POST" numDigits="{num_digits}" timeout="{timeout}">'


def _end_gather() -> str:
    return "  </Gather>"


def _hangup() -> str:
    return "  <Hangup/>"


def _caller_id(request_form) -> str:
    return request_form.get("From", "unknown")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return "ok", 200


@app.post("/voice/incoming")
def incoming():
    return _texml(
        _gather("/voice/menu"),
        _say(
            "Welcome to EU CivicConnect. "
            "Press 1 for the Porto Mobility consultation. "
            "Press 2 for the Digital ID consultation. "
            "Press 3 to hear the latest EU results. "
            "Press 0 to end the call."
        ),
        _end_gather(),
        _say("We did not receive your input. Goodbye!"),
        _hangup(),
    )


@app.post("/voice/menu")
def menu():
    digit = request.form.get("Digits", "")
    if digit == "1":
        return consult_tts("mobility_porto")
    elif digit == "2":
        return consult_tts("digital_id_pt")
    elif digit == "3":
        return results_tts()
    else:
        return _texml(_say("Goodbye! Thank you for participating."), _hangup())


def consult_tts(cid: str) -> Response:
    c = CONSULTATIONS[cid]
    caller = request.form.get("From", "unknown")
    already_voted = has_voted(caller, cid)
    voted_msg = " You have already voted on this consultation." if already_voted else ""
    return _texml(
        _gather(f"/voice/vote/{cid}"),
        _say(
            f"{c['level']} consultation: {c['title']}. "
            f"{c['summary']}"
            f"{voted_msg} "
            "Press 1 to support this proposal. "
            "Press 2 to oppose it. "
            "Press 0 to return to the main menu."
        ),
        _end_gather(),
        _say("We did not receive your input. Returning to main menu."),
        _say("Press 1 for the Porto Mobility consultation. Press 2 for Digital ID. Press 3 for EU results. Press 0 to end."),
        _hangup(),
    )


@app.post("/voice/vote/<cid>")
def vote(cid: str):
    digit = request.form.get("Digits", "")
    caller = request.form.get("From", "unknown")
    c = CONSULTATIONS.get(cid)
    if not c:
        return _texml(_say("Invalid consultation. Goodbye."), _hangup())

    if digit == "1":
        recorded = record_vote(caller, cid, "support")
        msg = "Your support has been recorded. Thank you!" if recorded else "You have already voted on this consultation."
    elif digit == "2":
        recorded = record_vote(caller, cid, "oppose")
        msg = "Your opposition has been recorded. Thank you!" if recorded else "You have already voted on this consultation."
    elif digit == "0":
        return _texml(
            _gather("/voice/menu"),
            _say("Press 1 for Porto Mobility, press 2 for Digital ID, press 3 for EU results, press 0 to end."),
            _end_gather(),
            _hangup(),
        )
    else:
        return _texml(_say("Invalid input. Goodbye."), _hangup())

    if has_voted_all(caller, CONSULTATION_IDS):
        eu = EU_RESULT
        eu_msg = (
            f"Congratulations! You have now participated in both consultations. "
            f"Here are the results of a recently closed European Union consultation: "
            f"{eu['title']}. "
            f"Over 2 point 3 million responses were received. "
            f"68 percent supported mandatory renovation targets. "
            f"The European Commission committed to a phased approach with dedicated financial support."
        )
        return _texml(_say(f"{msg} {eu_msg} Goodbye!"), _hangup())

    return _texml(
        _gather("/voice/menu"),
        _say(
            f"{msg} "
            "Press 1 for Porto Mobility, press 2 for Digital ID, press 3 for EU results, press 0 to end."
        ),
        _end_gather(),
        _say("Goodbye!"),
        _hangup(),
    )


def results_tts() -> Response:
    lines = ["Here are the current vote counts. "]
    for c in CONSULT_LIST:
        counts = get_vote_counts(c["id"])
        support = counts.get("support", 0)
        oppose = counts.get("oppose", 0)
        total = support + oppose
        if total:
            pct = int(support / total * 100)
            lines.append(
                f"{c['title']}: {support} in support, that is {pct} percent. "
                f"{oppose} in opposition, that is {100 - pct} percent. "
            )
        else:
            lines.append(f"{c['title']}: no votes recorded yet. ")
    lines.append("Thank you for using EU CivicConnect. Goodbye!")
    return _texml(_say(" ".join(lines)), _hangup())


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8200, debug=False)
