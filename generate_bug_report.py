from fpdf import FPDF, XPos, YPos
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "LibTracker_BugReport.pdf")

FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD    = "C:/Windows/Fonts/arialbd.ttf"
FONT_MONO    = "C:/Windows/Fonts/DejaVuSansMono_0.ttf"
FONT_MONO_B  = "C:/Windows/Fonts/DejaVuSansMono-Bold_0.ttf"

BUGS = [
    {
        "id": 1,
        "severity": "CRITICAL",
        "color": (220, 53, 69),
        "file": "backend/routes/reservations.py  line 83",
        "title": "Timezone-naive vs aware datetime comparison crash",
        "error": "if start < datetime.now():",
        "fix":   "if start < datetime.now(start.tzinfo or timezone.utc):",
        "desc": (
            "Comparing a timezone-aware datetime (e.g. sent as ISO 8601 with +03:00) "
            "against naive datetime.now() raises TypeError at runtime. "
            "The fix uses the incoming datetime's own tzinfo, falling back to UTC."
        ),
    },
    {
        "id": 2,
        "severity": "CRITICAL",
        "color": (220, 53, 69),
        "file": "backend/routes/libraries.py  line 87",
        "title": "int() conversion without error handling in create_library",
        "error": 'capacity = int(data.get("total_capacity", 0))',
        "fix": (
            "try:\n"
            '    capacity = int(data.get("total_capacity", 0))\n'
            "except (ValueError, TypeError):\n"
            '    return jsonify({"error": "total_capacity must be a valid number"}), 400'
        ),
        "desc": (
            "Passing a non-numeric string (e.g. \"abc\") causes an unhandled ValueError "
            "and returns a 500 Internal Server Error instead of a 400. "
            "Wrapped in try/except so invalid input is rejected cleanly."
        ),
    },
    {
        "id": 3,
        "severity": "CRITICAL",
        "color": (220, 53, 69),
        "file": "backend/routes/libraries.py  lines 134, 136",
        "title": "int() conversion without error handling in update_library",
        "error": (
            'lib.total_capacity   = int(data["total_capacity"])\n'
            'lib.current_occupancy = int(data["current_occupancy"])'
        ),
        "fix": (
            "try:\n"
            '    lib.total_capacity = int(data["total_capacity"])\n'
            "except (ValueError, TypeError):\n"
            '    return jsonify({"error": "total_capacity must be a valid number"}), 400\n'
            "\n"
            "try:\n"
            '    new_occ = int(data["current_occupancy"])\n'
            "except (ValueError, TypeError):\n"
            '    return jsonify({"error": "current_occupancy must be a valid number"}), 400'
        ),
        "desc": (
            "Same crash as bug #2 but in the update endpoint. "
            "Both fields are now validated with try/except before assignment."
        ),
    },
    {
        "id": 4,
        "severity": "LOGICAL BUG",
        "color": (255, 140, 0),
        "file": "backend/database.py  line 62",
        "title": "Admin email is not a valid email address",
        "error": 'admin_email = "admin"',
        "fix":   'admin_email = "admin@libtracker.edu"',
        "desc": (
            "The seed creates an admin user with the email string \"admin\", "
            "which is not a valid email format. Changed to admin@libtracker.edu "
            "so the field holds a properly formed address."
        ),
    },
    {
        "id": 5,
        "severity": "LOGICAL BUG",
        "color": (255, 140, 0),
        "file": "backend/database.py  line 128",
        "title": "Seed generates future timestamps for UsageStatistics",
        "error": "recorded = now - timedelta(days=day_offset, hours=(now.hour - hour))",
        "fix": (
            "recorded = (now - timedelta(days=day_offset)).replace(\n"
            "    hour=hour, minute=0, second=0, microsecond=0\n"
            ")\n"
            "if recorded > now:\n"
            "    continue"
        ),
        "desc": (
            "When now.hour < hour (e.g. it is 9 AM and hour=14), the subtraction "
            "becomes negative, effectively adding hours and creating a future timestamp. "
            "Fixed by using .replace() to set the exact hour on the past date, then "
            "skipping any slot still in the future."
        ),
    },
    {
        "id": 6,
        "severity": "LOGICAL BUG",
        "color": (255, 140, 0),
        "file": "backend/routes/libraries.py  lines 142-146",
        "title": "Capacity update resets available_seats ignoring active reservations",
        "error": (
            "area.total_seats    = new_seats_per_area\n"
            "area.available_seats = new_seats_per_area  # ignores reservations"
        ),
        "fix": (
            "active_count = Reservation.query.filter_by(\n"
            '    study_area_id=area.id, status="active"\n'
            ").count()\n"
            "area.total_seats     = new_seats_per_area\n"
            "area.available_seats = max(0, new_seats_per_area - active_count)"
        ),
        "desc": (
            "When an admin changes a library's total capacity, all study areas had "
            "their available_seats reset to the new per-area value, ignoring existing "
            "active reservations. A fully booked area would suddenly appear empty. "
            "Fixed by computing available seats from the real active reservation count."
        ),
    },
    {
        "id": 7,
        "severity": "LOGICAL BUG",
        "color": (255, 140, 0),
        "file": "backend/routes/libraries.py  line 136",
        "title": "current_occupancy can exceed total_capacity",
        "error": 'lib.current_occupancy = int(data["current_occupancy"])',
        "fix": (
            "if new_occ > lib.total_capacity:\n"
            '    return jsonify({"error": "current_occupancy cannot exceed capacity"}), 400\n'
            "lib.current_occupancy = new_occ"
        ),
        "desc": (
            "No upper-bound check allowed an admin to set current_occupancy to any value, "
            "making occupancy_percentage return values above 100%. "
            "Added validation against the already-updated total_capacity."
        ),
    },
    {
        "id": 8,
        "severity": "LOGICAL BUG",
        "color": (255, 140, 0),
        "file": "backend/routes/reservations.py  lines 103-107",
        "title": "available_seats counter becomes permanently inaccurate",
        "error": (
            "if area.available_seats > 0:\n"
            "    area.available_seats -= 1"
        ),
        "fix": (
            "db.session.flush()\n"
            "active_count = Reservation.query.filter_by(\n"
            '    study_area_id=study_area_id, status="active"\n'
            ").count()\n"
            "area.available_seats = max(0, area.total_seats - active_count)"
        ),
        "desc": (
            "When available_seats reached 0, the counter stopped decrementing while "
            "new reservations were still being created. After cancellations restored the "
            "counter, subsequent bookings left it out of sync. "
            "Fixed by recomputing available_seats from actual active reservation count. "
            "The same fix was applied to cancel_reservation."
        ),
    },
    {
        "id": 9,
        "severity": "PERFORMANCE",
        "color": (40, 167, 69),
        "file": "backend/routes/feedback.py  lines 126-129",
        "title": "N+1 query: one DB call per feedback row",
        "error": (
            "for fb in feedbacks:\n"
            "    user = User.query.get(fb.user_id)  # 1 query per row"
        ),
        "fix": (
            "feedbacks = (\n"
            "    Feedback.query\n"
            "    .options(joinedload(Feedback.user))\n"
            "    ...\n"
            ")\n"
            "for fb in feedbacks:\n"
            '    d["user_name"] = fb.user.name if fb.user else "Anonim"'
        ),
        "desc": (
            "With the default limit of 20 feedbacks, this loop fired 21 separate SQL "
            "queries (one per row plus one for the list). Replaced with a single JOIN "
            "using SQLAlchemy's joinedload(), reducing it to 1 query regardless of "
            "the number of results."
        ),
    },
]

SEV_ORDER = {"CRITICAL": 0, "LOGICAL BUG": 1, "PERFORMANCE": 2}


class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 30, 50)
        self.rect(0, 0, 210, 22, "F")
        self.set_font("Bold", size=14)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 5)
        self.cell(0, 12, "LibTracker  -  Bug Report & Fixes")
        self.set_font("Regular", size=9)
        self.set_text_color(180, 180, 180)
        self.set_xy(10, 14)
        self.cell(0, 6, "9 issues found and resolved  |  2026-04-27")
        self.ln(8)

    def footer(self):
        self.set_y(-12)
        self.set_font("Regular", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()} / {{nb}}", align="C")

    def code_block(self, label, code_text, bg):
        self.set_font("Bold", size=8)
        self.set_text_color(80, 80, 80)
        self.cell(
            0, 5, label,
            new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        self.set_fill_color(*bg)
        self.set_font("Mono", size=8)
        self.set_text_color(30, 30, 30)
        w = self.w - self.l_margin - self.r_margin
        for line in code_text.split("\n"):
            self.set_x(self.l_margin)
            self.cell(w, 5, line, fill=True,
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)


def build_pdf():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    pdf.add_font("Regular", style="",  fname=FONT_REGULAR)
    pdf.add_font("Bold",    style="",  fname=FONT_BOLD)
    pdf.add_font("Mono",    style="",  fname=FONT_MONO)
    pdf.add_font("MonoBold",style="",  fname=FONT_MONO_B)

    # ── Cover / summary page ────────────────────────────────────────────────
    pdf.add_page()

    pdf.set_font("Bold", size=10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, "Summary of All Issues",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    col_w = [10, 98, 44, 38]
    hdrs  = ["#", "Title", "File", "Severity"]

    pdf.set_draw_color(200, 200, 200)
    pdf.set_font("Bold", size=8)
    pdf.set_fill_color(230, 230, 240)
    pdf.set_text_color(30, 30, 30)
    for i, h in enumerate(hdrs):
        pdf.cell(col_w[i], 6, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Regular", size=7.5)
    for b in BUGS:
        r, g, bl = b["color"]
        pdf.set_text_color(r, g, bl)
        pdf.cell(col_w[0], 5.5, str(b["id"]), border=1)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(col_w[1], 5.5, b["title"][:62], border=1)
        pdf.cell(col_w[2], 5.5, b["file"].split("  ")[0], border=1)
        pdf.set_text_color(r, g, bl)
        pdf.cell(col_w[3], 5.5, b["severity"], border=1)
        pdf.set_text_color(30, 30, 30)
        pdf.ln()

    # ── One page per bug ────────────────────────────────────────────────────
    for b in BUGS:
        pdf.add_page()

        r, g, bl = b["color"]
        pdf.set_fill_color(r, g, bl)
        bar_w = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.rect(pdf.l_margin, pdf.get_y(), bar_w, 10, "F")
        pdf.set_font("Bold", size=10)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 10, f"  #{b['id']}  {b['title']}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(2)

        # meta row
        pdf.set_font("Bold", size=8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(25, 5, "Severity:")
        pdf.set_text_color(r, g, bl)
        pdf.cell(0, 5, b["severity"],
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_text_color(100, 100, 100)
        pdf.cell(25, 5, "Location:")
        pdf.set_font("Regular", size=8)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 5, b["file"],
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # description
        pdf.set_font("Bold", size=8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, "Description",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Regular", size=8.5)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, b["desc"])
        pdf.ln(3)

        # code blocks
        pdf.code_block("Before  (buggy code):", b["error"], (255, 235, 235))
        pdf.ln(1)
        pdf.code_block("After   (fixed code):", b["fix"],   (230, 255, 230))

    pdf.output(OUTPUT)
    print(f"PDF saved: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
