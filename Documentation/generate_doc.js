const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, Header, Footer, LevelFormat, ExternalHyperlink
} = require('C:/Users/s.ketenoglu/AppData/Roaming/npm/node_modules/docx');
const fs = require('fs');

// ─── COLORS ───────────────────────────────────────────────
const DARK_BLUE  = "1A1F5E";
const MID_BLUE   = "4F6EF7";
const LIGHT_BLUE = "EEF1FF";
const GREEN      = "166534";
const GREEN_BG   = "DCFCE7";
const RED        = "7F1D1D";
const RED_BG     = "FEE2E2";
const YELLOW_BG  = "FEF9C3";
const YELLOW_TXT = "854D0E";
const GRAY       = "64748B";
const BORDER_CLR = "CBD5E1";
const CODE_BG    = "F1F5F9";

// ─── HELPERS ──────────────────────────────────────────────
const border = (color = BORDER_CLR) => ({
  top:    { style: BorderStyle.SINGLE, size: 4, color },
  bottom: { style: BorderStyle.SINGLE, size: 4, color },
  left:   { style: BorderStyle.SINGLE, size: 4, color },
  right:  { style: BorderStyle.SINGLE, size: 4, color },
});

const cellMargins = { top: 80, bottom: 80, left: 140, right: 140 };

const sp = (before = 0, after = 0) => ({ spacing: { before, after } });

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, color: DARK_BLUE, font: "Arial", size: 30 })],
    ...sp(320, 160),
  });
}
function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, color: MID_BLUE, font: "Arial", size: 24 })],
    ...sp(280, 120),
  });
}
function heading3(text, color = DARK_BLUE) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, color, font: "Arial", size: 22 })],
    ...sp(240, 100),
  });
}
function body(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 20, ...opts })],
    ...sp(60, 60),
  });
}
function space(size = 100) {
  return new Paragraph({ children: [new TextRun("")], spacing: { before: size, after: 0 } });
}
function code(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Consolas", size: 18, color: "1E293B" })],
    spacing: { before: 40, after: 40 },
    shading: { fill: CODE_BG, type: ShadingType.CLEAR },
    indent: { left: 400 },
  });
}

function numberedItem(text, n, color = DARK_BLUE) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    children: [new TextRun({ text, font: "Arial", size: 20, color })],
    ...sp(60, 60),
  });
}
function bulletItem(text, bold_prefix = "", color = DARK_BLUE) {
  const runs = [];
  if (bold_prefix) {
    runs.push(new TextRun({ text: bold_prefix + " ", font: "Arial", size: 20, bold: true, color }));
    runs.push(new TextRun({ text, font: "Arial", size: 20, color: "1E293B" }));
  } else {
    runs.push(new TextRun({ text, font: "Arial", size: 20, color: "1E293B" }));
  }
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: runs,
    ...sp(60, 60),
  });
}

function alertBox(label, text, bgColor, textColor) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    borders: {
      top:           { style: BorderStyle.SINGLE, size: 8, color: textColor },
      bottom:        { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      left:          { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      right:         { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      insideH:       { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      insideV:       { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
    },
    rows: [new TableRow({ children: [
      new TableCell({
        shading: { fill: bgColor, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        width: { size: 9360, type: WidthType.DXA },
        borders: {
          top:    { style: BorderStyle.SINGLE, size: 12, color: textColor },
          bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
          left:   { style: BorderStyle.THICK, size: 24, color: textColor },
          right:  { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        },
        children: [new Paragraph({
          children: [
            new TextRun({ text: label + "  ", font: "Arial", size: 20, bold: true, color: textColor }),
            new TextRun({ text, font: "Arial", size: 20, color: "1E293B" }),
          ],
          spacing: { before: 0, after: 0 },
        })]
      })
    ]})],
  });
}

function divider() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER_CLR, space: 1 } },
    children: [new TextRun("")],
    spacing: { before: 120, after: 120 },
  });
}

// ─── HEADER TABLE (cover-style) ───────────────────────────
function coverHeader() {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({ children: [
      new TableCell({
        shading: { fill: DARK_BLUE, type: ShadingType.CLEAR },
        margins: { top: 360, bottom: 360, left: 400, right: 400 },
        width: { size: 9360, type: WidthType.DXA },
        borders: border(DARK_BLUE),
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "LibTracker", font: "Arial Black", size: 52, bold: true, color: "FFFFFF" })],
            spacing: { before: 0, after: 80 },
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Ekip Görev Dağılımı Belgesi", font: "Arial", size: 32, color: "AAB4D4" })],
            spacing: { before: 0, after: 80 },
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Rebs Dev  |  Hafta 9\u201314  |  Nisan 2026", font: "Arial", size: 22, color: "7C9EFF" })],
            spacing: { before: 0, after: 0 },
          }),
        ]
      })
    ]})],
  });
}

// ─── PERSON TASK TABLE ─────────────────────────────────────
function personHeader(name, role, branch, accentColor, initials) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1200, 8160],
    rows: [new TableRow({ children: [
      new TableCell({
        shading: { fill: accentColor, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 140, right: 140 },
        width: { size: 1200, type: WidthType.DXA },
        borders: border(accentColor),
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: initials, font: "Arial Black", size: 36, bold: true, color: "FFFFFF" })],
        })]
      }),
      new TableCell({
        shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 180, right: 140 },
        width: { size: 8160, type: WidthType.DXA },
        borders: { ...border(BORDER_CLR), left: { style: BorderStyle.SINGLE, size: 8, color: accentColor } },
        children: [
          new Paragraph({ children: [new TextRun({ text: name, font: "Arial", size: 26, bold: true, color: DARK_BLUE })], spacing: { before: 0, after: 40 } }),
          new Paragraph({ children: [new TextRun({ text: role, font: "Arial", size: 20, color: GRAY })], spacing: { before: 0, after: 40 } }),
          new Paragraph({ children: [
            new TextRun({ text: "Branch: ", font: "Consolas", size: 18, bold: true, color: GRAY }),
            new TextRun({ text: branch, font: "Consolas", size: 18, color: MID_BLUE }),
          ], spacing: { before: 0, after: 0 } }),
        ]
      }),
    ]})],
  });
}

function gitStepsTable(steps) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({ children: [
        new TableCell({
          shading: { fill: "1E293B", type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 200, right: 200 },
          width: { size: 9360, type: WidthType.DXA },
          borders: border("334155"),
          children: [new Paragraph({
            children: [new TextRun({ text: "  GitHub\u2019a Push Ad\u0131mlar\u0131", font: "Arial", size: 18, bold: true, color: "7C9EFF" })],
            spacing: { before: 0, after: 0 },
          })]
        })
      ]}),
      ...steps.map(s => new TableRow({ children: [
        new TableCell({
          shading: { fill: "0F172A", type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 200, right: 200 },
          width: { size: 9360, type: WidthType.DXA },
          borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, left: { style: BorderStyle.SINGLE, size: 4, color: "334155" }, right: { style: BorderStyle.SINGLE, size: 4, color: "334155" } },
          children: [new Paragraph({
            children: [new TextRun({ text: s, font: "Consolas", size: 18, color: "86EFAC" })],
            spacing: { before: 0, after: 0 },
          })]
        })
      ]})),
      new TableRow({ children: [
        new TableCell({
          shading: { fill: "0F172A", type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 200, right: 200 },
          width: { size: 9360, type: WidthType.DXA },
          borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, bottom: { style: BorderStyle.SINGLE, size: 4, color: "334155" }, left: { style: BorderStyle.SINGLE, size: 4, color: "334155" }, right: { style: BorderStyle.SINGLE, size: 4, color: "334155" } },
          children: [new Paragraph({ children: [new TextRun("")], spacing: { before: 0, after: 0 } })]
        })
      ]})
    ],
  });
}

// ─── WEEKLY TABLE ─────────────────────────────────────────
function weeklyTable() {
  const headerCell = (text) => new TableCell({
    shading: { fill: DARK_BLUE, type: ShadingType.CLEAR },
    margins: cellMargins,
    borders: border(DARK_BLUE),
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: "FFFFFF" })] })]
  });

  const dataCell = (text, fill = "FFFFFF", bold = false, color = "1E293B", colWidth) => new TableCell({
    shading: { fill, type: ShadingType.CLEAR },
    margins: cellMargins,
    borders: border(BORDER_CLR),
    width: { size: colWidth, type: WidthType.DXA },
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 19, bold, color })] })]
  });

  const rows = [
    { w: "Hafta 9", d: "Nis 25\u2013May 1", h: "Proje iskeleti + DB modelleri + Auth ba\u015flang\u0131c\u0131", r: "Sirac + Emre \u26a0\ufe0f" },
    { w: "Hafta 10", d: "May 2\u20138", h: "T\u00fcm core API endpoint\u2019leri + Frontend ba\u011flant\u0131s\u0131 ba\u015fl\u0131yor", r: "Herkes" },
    { w: "Hafta 11", d: "May 9\u201315", h: "End-to-end entegrasyon tamamland\u0131 + Testler \u00e7al\u0131\u015f\u0131yor", r: "Bar\u0131\u015f + Reis \u26a0\ufe0f" },
    { w: "Hafta 12", d: "May 16\u201322", h: "Tam test suite + Security review + Bug fix sprint", r: "Herkes" },
    { w: "Hafta 13", d: "May 23\u201329", h: "Final rapor yaz\u0131m\u0131 + README g\u00fcncelleme + Demo son hali", r: "Herkes" },
    { w: "Hafta 14", d: "May 30\u2013Haz 5", h: "Final teslim + Sunum provas\u0131 (2 kez) \ud83c\udfc1", r: "Herkes" },
  ];

  const fills = ["EEF1FF","F8FAFF","EEF1FF","F8FAFF","EEF1FF","DCFCE7"];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1200, 1360, 4600, 2200],
    rows: [
      new TableRow({ children: [headerCell("Hafta"), headerCell("Tarih"), headerCell("Hedef"), headerCell("Sorumlu")] }),
      ...rows.map((r, i) => new TableRow({ children: [
        dataCell(r.w, fills[i], true, DARK_BLUE, 1200),
        dataCell(r.d, fills[i], false, GRAY, 1360),
        dataCell(r.h, fills[i], false, "1E293B", 4600),
        dataCell(r.r, fills[i], false, "1E293B", 2200),
      ]})),
    ],
  });
}

// ─── DOCUMENT ─────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
      {
        reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
      {
        reference: "numbers2",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
      {
        reference: "numbers3",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
      {
        reference: "numbers4",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
      {
        reference: "numbers5",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
    ],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: DARK_BLUE },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: MID_BLUE },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 },
      }
    },
    headers: {
      default: new Header({ children: [
        new Paragraph({
          children: [
            new TextRun({ text: "LibTracker \u2013 Ekip G\u00f6rev Da\u011f\u0131l\u0131m\u0131 Belgesi", font: "Arial", size: 18, color: GRAY }),
            new TextRun({ text: "\t\tRebs Dev | Nisan 2026", font: "Arial", size: 18, color: GRAY }),
          ],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER_CLR, space: 1 } },
          tabStops: [{ type: "right", position: 9026 }],
        })
      ]})
    },
    footers: {
      default: new Footer({ children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Sayfa ", font: "Arial", size: 16, color: GRAY }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: GRAY }),
            new TextRun({ text: " / ", font: "Arial", size: 16, color: GRAY }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 16, color: GRAY }),
          ],
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: BORDER_CLR, space: 1 } },
        })
      ]})
    },
    children: [

      // ── COVER ────────────────────────────────────────────
      coverHeader(),
      space(200),

      // Team members row
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2256, 2256, 2257, 2257],
        rows: [new TableRow({ children: [
          ...[
            ["SK", "Sirac Ketenoglu", "Backend Lead", "22C55E"],
            ["ET", "Emre Turan", "Auth & Feedback", "4F6EF7"],
            ["RY", "Reis Y\u0131ld\u0131z", "Frontend Lead", "F59E0B"],
            ["BK", "Bar\u0131\u015f K\u00fc\u00e7\u00fckk\u0131ya", "Test & Rezervasyon", "EF4444"],
          ].map(([init, name, role, col]) => new TableCell({
            shading: { fill: "F8FAFF", type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 120, right: 120 },
            borders: { top: { style: BorderStyle.SINGLE, size: 12, color: col }, bottom: border(BORDER_CLR).bottom, left: border(BORDER_CLR).left, right: border(BORDER_CLR).right },
            children: [
              new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: init, font: "Arial Black", size: 28, bold: true, color: col })], spacing: { before: 0, after: 60 } }),
              new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: name, font: "Arial", size: 19, bold: true, color: DARK_BLUE })], spacing: { before: 0, after: 40 } }),
              new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: role, font: "Arial", size: 17, color: GRAY })], spacing: { before: 0, after: 0 } }),
            ]
          }))
        ]})],
      }),

      space(300),
      divider(),

      // ── SECTION 1 ─────────────────────────────────────────
      heading1("1. Proje \u00d6zeti"),
      body("LibTracker, \u00fcniversite k\u00fct\u00fcphanelerinin ve \u00e7al\u0131\u015fma alanlar\u0131n\u0131n anl\u0131k doluluk seviyelerini izleyen, y\u00f6neten ve g\u00f6r\u00fcnt\u00fcleyen bir uygulamad\u0131r."),
      space(80),

      // Features table
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2256, 6770],
        rows: [
          ...[
            ["01 \ud83d\udcca", "Ger\u00e7ek Zamanl\u0131 Doluluk Panosu \u2013 T\u00fcm konumlar\u0131n anl\u0131k doluluk y\u00fczdesini g\u00f6sterir."],
            ["02 \ud83d\udcac", "Kullan\u0131c\u0131 Geri Bildirim Sistemi \u2013 Do\u011frulanm\u0131\u015f \u00f6\u011frenciler aktif doluluk g\u00fcncellemesi yapabilir."],
            ["03 \ud83d\udcc5", "\u00c7al\u0131\u015fma Alan\u0131 Rezervasyon Sistemi \u2013 Yo\u011fun d\u00f6nemlerde koltuk \u00f6nceden rezerve edilebilir."],
            ["04 \ud83d\udcc8", "Admin \u0130statistik Panosu \u2013 G\u00fcnl\u00fck zirve saatleri i\u00e7in g\u00f6rsel grafikler (y\u00f6netim i\u00e7in)."],
          ].map(([num, desc], i) => new TableRow({ children: [
            new TableCell({
              shading: { fill: i % 2 === 0 ? LIGHT_BLUE : "FFFFFF", type: ShadingType.CLEAR },
              margins: cellMargins, borders: border(BORDER_CLR),
              width: { size: 2256, type: WidthType.DXA },
              children: [new Paragraph({ children: [new TextRun({ text: num, font: "Arial", size: 19, bold: true, color: DARK_BLUE })] })]
            }),
            new TableCell({
              shading: { fill: i % 2 === 0 ? LIGHT_BLUE : "FFFFFF", type: ShadingType.CLEAR },
              margins: cellMargins, borders: border(BORDER_CLR),
              width: { size: 6770, type: WidthType.DXA },
              children: [new Paragraph({ children: [new TextRun({ text: desc, font: "Arial", size: 19, color: "1E293B" })] })]
            }),
          ]}))
        ],
      }),

      space(120),
      new Paragraph({
        children: [
          new TextRun({ text: "GitHub Repo: ", font: "Arial", size: 20, bold: true, color: GRAY }),
          new ExternalHyperlink({ link: "https://github.com/emre-data-turan/LibTracker", children: [new TextRun({ text: "https://github.com/emre-data-turan/LibTracker", font: "Consolas", size: 19, color: MID_BLUE, underline: {} })] }),
        ],
        spacing: { before: 80, after: 60 },
      }),
      new Paragraph({
        children: [
          new TextRun({ text: "Mimari: ", font: "Arial", size: 20, bold: true, color: GRAY }),
          new TextRun({ text: "Katmanl\u0131 Mimari (Layered Architecture)    ", font: "Arial", size: 20, color: "1E293B" }),
          new TextRun({ text: "Tasar\u0131m Deseni: ", font: "Arial", size: 20, bold: true, color: GRAY }),
          new TextRun({ text: "Singleton (SystemDatabase ba\u011flant\u0131s\u0131 i\u00e7in)", font: "Arial", size: 20, color: "1E293B" }),
        ],
        spacing: { before: 0, after: 0 },
      }),

      space(200),
      divider(),

      // ── SECTION 2 ─────────────────────────────────────────
      heading1("2. Genel Git Kurallar\u0131 (Herkes Uyacak)"),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "Her \u00f6zellik i\u00e7in ayr\u0131 branch a\u00e7\u0131lacak.", font: "Arial", size: 20 }), new TextRun({ text: "  \u00d6rnek: ", font: "Arial", size: 20, color: GRAY }), new TextRun({ text: "feature/auth-system", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: ", ", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: "feature/reservation-api", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "main", font: "Consolas", size: 19, bold: true, color: RED }), new TextRun({ text: " branch'ine direkt push ", font: "Arial", size: 20 }), new TextRun({ text: "YAPILMAYACAK.", font: "Arial", size: 20, bold: true, color: RED }), new TextRun({ text: " Her zaman PR (Pull Request) a\u00e7\u0131lacak.", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "PR a\u00e7\u0131lmadan \u00f6nce kendi branch'inde test yap\u0131lacak.", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "En az 1 ki\u015fi PR'\u0131 review etmeden merge ", font: "Arial", size: 20 }), new TextRun({ text: "YAPILMAYACAK.", font: "Arial", size: 20, bold: true, color: RED })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "Commit mesajlar\u0131 anlaml\u0131 yaz\u0131lacak.  \u00d6rnek: ", font: "Arial", size: 20 }), new TextRun({ text: '"Add JWT authentication endpoint"', font: "Consolas", size: 19, color: GRAY })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "Jira'\u0131daki g\u00f6rev tamamland\u0131\u011f\u0131nda ", font: "Arial", size: 20 }), new TextRun({ text: '"Done"', font: "Arial", size: 20, bold: true, color: GREEN }), new TextRun({ text: " olarak i\u015faretlenecek.", font: "Arial", size: 20 })], ...sp(60,60) }),

      space(200),
      divider(),

      // ── SECTION 3 ─────────────────────────────────────────
      heading1("3. Ki\u015fi Baz\u0131 G\u00f6rev Da\u011f\u0131l\u0131m\u0131"),

      // 3.1 Sirac
      heading2("3.1 Sirac Ketenoglu \u2013 Backend Lead"),
      space(40),
      personHeader("Sirac Ketenoglu", "Backend Lead", "feature/backend-core", "22C55E", "SK"),
      space(120),
      heading3("G\u00f6revler"),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "Flask/FastAPI proje iskeletini kur (klas\u00f6r yap\u0131s\u0131, requirements.txt)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "SQLAlchemy ile veritaban\u0131 modellerini olu\u015ftur: ", font: "Arial", size: 20 }), new TextRun({ text: "User, Library, StudyArea, Reservation, Feedback, UsageStatistics", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "Singleton design pattern'\u0131 ger\u00e7ek Python koduyla implemente et (", font: "Arial", size: 20 }), new TextRun({ text: "SystemDatabase", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: " s\u0131n\u0131f\u0131)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "Doluluk (Occupancy) API endpoint\u2019lerini yaz: ", font: "Arial", size: 20 }), new TextRun({ text: "GET /libraries, GET /libraries/{id}/occupancy", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "Admin istatistik API\u2019sini yaz: ", font: "Arial", size: 20 }), new TextRun({ text: "GET /stats/peak-hours, GET /stats/daily-usage", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "GitHub Actions ile basit CI pipeline kur", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "API dok\u00fcmantasyonunu yaz (Swagger veya README\u2019de endpoint listesi)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers2", level: 0 }, children: [new TextRun({ text: "Sprint 2 ve Sprint 3 Jira backlog\u2019unu olu\u015ftur", font: "Arial", size: 20 })], ...sp(60,60) }),
      space(120),
      gitStepsTable([
        "git checkout -b feature/backend-core",
        "# Kodunu yaz ve test et",
        'git add .',
        'git commit -m "Add Flask backend core and DB models"',
        "git push origin feature/backend-core",
        "# GitHub'da Pull Request a\u00e7, Emre veya Bar\u0131\u015f'\u0131 reviewer olarak ekle",
      ]),

      space(300),

      // 3.2 Emre
      heading2("3.2 Emre Turan \u2013 Auth & Feedback Sistemi"),
      space(40),
      personHeader("Emre Turan", "Auth & Feedback Sistemi", "feature/auth-and-feedback", "4F6EF7", "ET"),
      space(120),
      heading3("G\u00f6revler"),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "JWT tabanl\u0131 Authentication sistemini kur: ", font: "Arial", size: 20 }), new TextRun({ text: "POST /auth/register, POST /auth/login, POST /auth/logout", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "\u00d6\u011frenci do\u011frulama mekanizmas\u0131n\u0131 implemente et (yaln\u0131zca \u00fcniversite e-postas\u0131)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "Feedback API endpoint\u2019lerini yaz: ", font: "Arial", size: 20 }), new TextRun({ text: "POST /feedback, GET /feedback/{libraryId}", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "Fake feedback \u00f6nleme mekanizmas\u0131n\u0131 yaz (IP bazl\u0131 rate limiting, basit filtre)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "\u0130statistik ve raporlama API\u2019sini Sirac ile koordineli yaz", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "Security review yap: SQL injection, auth bypass, input validation", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers3", level: 0 }, children: [new TextRun({ text: "Final raporu i\u00e7in \u201cG\u00fcvenlik ve Kimlik Do\u011frulama\u201d b\u00f6l\u00fcm\u00fcn\u00fc yaz", font: "Arial", size: 20 })], ...sp(60,60) }),
      space(120),
      gitStepsTable([
        "git checkout -b feature/auth-and-feedback",
        "# Kodunu yaz ve test et",
        "git add .",
        'git commit -m "Add JWT auth system and feedback API"',
        "git push origin feature/auth-and-feedback",
        "# GitHub'da Pull Request a\u00e7, Sirac'\u0131 reviewer olarak ekle",
      ]),

      space(300),

      // 3.3 Reis
      heading2("3.3 Reis Y\u0131ld\u0131z \u2013 Frontend Lead"),
      space(40),
      personHeader("Reis Y\u0131ld\u0131z", "Frontend Lead", "feature/frontend-integration", "F59E0B", "RY"),
      space(120),
      heading3("G\u00f6revler"),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Mevcut demo.html\u2019i ger\u00e7ek backend API\u2019sine ba\u011fla (JavaScript ", font: "Arial", size: 20 }), new TextRun({ text: "fetch", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: " ile)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Dashboard sayfas\u0131n\u0131 ", font: "Arial", size: 20 }), new TextRun({ text: "GET /libraries", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: " endpoint\u2019inden canl\u0131 veriyle \u00e7al\u0131\u015ft\u0131r", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Reservation formunu ", font: "Arial", size: 20 }), new TextRun({ text: "POST /reservations", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: " API\u2019sine ba\u011fla", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Feedback formunu ", font: "Arial", size: 20 }), new TextRun({ text: "POST /feedback", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: " API\u2019sine ba\u011fla", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Admin panosunu ", font: "Arial", size: 20 }), new TextRun({ text: "GET /stats", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: " API\u2019sinden ger\u00e7ek grafiklerle \u00e7al\u0131\u015ft\u0131r", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Mobil uyumluluk ve cross-browser testleri yap", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "README.md dosyas\u0131n\u0131 tamamla: kurulum ad\u0131mlar\u0131, proje a\u00e7\u0131klamas\u0131, ekip bilgisi, ekran g\u00f6r\u00fcnt\u00fcleri", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers4", level: 0 }, children: [new TextRun({ text: "Final sunumu i\u00e7in demo\u2019nun son halini haz\u0131rla", font: "Arial", size: 20 })], ...sp(60,60) }),
      space(120),
      gitStepsTable([
        "git checkout -b feature/frontend-integration",
        "# Kodunu yaz ve test et",
        "git add .",
        'git commit -m "Connect frontend dashboard to live API"',
        "git push origin feature/frontend-integration",
        "# GitHub'da Pull Request a\u00e7, Sirac'\u0131 reviewer olarak ekle",
      ]),

      space(300),

      // 3.4 Barış
      heading2("3.4 Bar\u0131\u015f K\u00fc\u00e7\u00fckk\u0131ya \u2013 Test & Rezervasyon Sistemi"),
      space(40),
      personHeader("Bar\u0131\u015f K\u00fc\u00e7\u00fckk\u0131ya", "Test & Rezervasyon Sistemi", "feature/reservation-and-tests", "EF4444", "BK"),
      space(120),
      heading3("G\u00f6revler"),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "Rezervasyon API endpoint\u2019lerini yaz: ", font: "Arial", size: 20 }), new TextRun({ text: "POST /reservations, GET /reservations/{userId}, DELETE /reservations/{id}", font: "Consolas", size: 19, color: MID_BLUE })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "\u00c7ak\u0131\u015fan rezervasyon kontrol\u00fcn\u00fc implemente et (ayn\u0131 koltuk, ayn\u0131 saat)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "pytest test ortam\u0131n\u0131 kur (", font: "Arial", size: 20 }), new TextRun({ text: "conftest.py", font: "Consolas", size: 19, color: MID_BLUE }), new TextRun({ text: ", fixtures)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "Authentication ak\u0131\u015f\u0131 i\u00e7in unit testler yaz (en az 5 test)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "Rezervasyon sistemi i\u00e7in unit ve entegrasyon testleri yaz (en az 8 test)", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "T\u00fcm test suite\u2019i \u00e7al\u0131\u015ft\u0131r, hata raporu haz\u0131rla", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "Final raporu i\u00e7in \u201cTest ve Do\u011frulama\u201d b\u00f6l\u00fcm\u00fcn\u00fc yaz", font: "Arial", size: 20 })], ...sp(60,60) }),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "Sistem Do\u011frulama raporunu haz\u0131rla (Hafta 12 teslimi)", font: "Arial", size: 20 })], ...sp(60,60) }),
      space(120),
      gitStepsTable([
        "git checkout -b feature/reservation-and-tests",
        "# Kodunu yaz ve testleri \u00e7al\u0131\u015ft\u0131r",
        "git add .",
        'git commit -m "Add reservation API and pytest test suite"',
        "git push origin feature/reservation-and-tests",
        "# GitHub'da Pull Request a\u00e7, Emre'yi reviewer olarak ekle",
      ]),

      space(300),
      new Paragraph({ numbering: { reference: "numbers5", level: 0 }, children: [new TextRun({ text: "Final raporu i\u00e7in \u201cG\u00fcvenlik ve Kimlik Do\u011frulama\u201d b\u00f6l\u00fcm\u00fcn\u00fc yaz", font: "Arial", size: 20 })], ...sp(60,60) }),
      space(120),
      gitStepsTable([
        "git checkout -b feature/auth-and-feedback",
        "# Kodunu yaz ve test et",
        "git add .",
        'git commit -m "Add JWT auth system and feedback API"',
        "git push origin feature/auth-and-feedback",
        "# GitHub'da Pull Request a\u00e7, Reis'i reviewer olarak ekle",
      ]),

      space(200),
      divider(),

      // ── SECTION 4 ─────────────────────────────────────────
      heading1("4. Haftal\u0131k Takvim"),
      space(80),
      weeklyTable(),

      space(200),
      divider(),

      // ── SECTION 5 ─────────────────────────────────────────
      heading1("5. Tamamlanma Kriteri (Definition of Done)"),
      body("Bir g\u00f6rev a\u015fa\u011f\u0131daki t\u00fcm ko\u015fullari sa\u011fland\u0131\u011f\u0131nda \u201cDone\u201d say\u0131l\u0131r:"),
      space(60),
      bulletItem("Kod local\u2019de \u00e7al\u0131\u015f\u0131yor ve test edilmi\u015f"),
      bulletItem("Unit test yaz\u0131lm\u0131\u015f (ilgili \u00f6zellik i\u00e7in)"),
      bulletItem("PR a\u00e7\u0131lm\u0131\u015f ve en az 1 ki\u015fi taraf\u0131ndan review edilmi\u015f"),
      bulletItem("Jira g\u00f6revi \u201cDone\u201d olarak i\u015faretlenmi\u015f"),
      bulletItem("Commit ge\u00e7mi\u015fi temiz ve anlaml\u0131 mesajlar i\u00e7eriyor"),
      bulletItem("Ba\u015fka bir branch\u2019in kodu bozulmad\u0131 (integration test ge\u00e7ti)"),

      space(200),
      divider(),

      // ── SECTION 6 ─────────────────────────────────────────
      heading1("6. \u00d6nemli Notlar"),
      space(80),
      alertBox("\u26a0\ufe0f UYARI:", "Bu hafta (Hafta 9) backend iskeleti kurulmadan di\u011fer t\u00fcm g\u00f6revler bloke olacak. Emre ve Bar\u0131\u015f bu haftan\u0131n \u00f6nceliklisi.", RED_BG, "991B1B"),
      space(120),
      alertBox("\ud83d\udccc NOT:", "Ger\u00e7ek k\u00fct\u00fcphane sens\u00f6r verisi olmad\u0131\u011f\u0131 i\u00e7in sistem seed data ve sim\u00fclasyon kullanacak. Bu normal ve kabul edilebilir \u2013 final raporda \u201cgelecek \u00e7al\u0131\u015fma\u201d olarak belirtilecek.", YELLOW_BG, YELLOW_TXT),
      space(120),
      alertBox("\ud83d\udccc NOT:", "Fake feedback \u00f6nleme i\u00e7in karma\u015f\u0131k ML bazl\u0131 \u00e7\u00f6z\u00fcme gerek yok. Basit rate limiting (ayn\u0131 kullan\u0131c\u0131dan 30 dakikada 1 feedback) yeterli.", YELLOW_BG, YELLOW_TXT),
      space(120),
      alertBox("\ud83d\udcde \u0130LET\u0130\u015e\u0130M:", "Blocker varsa ayn\u0131 g\u00fcn t\u00fcm ekibe bildirin. Haftal\u0131k durum toplant\u0131s\u0131 yap\u0131n (30 dakika yeterli).", GREEN_BG, "166534"),

      space(200),
      divider(),

      // ── SECTION 7 ─────────────────────────────────────────
      heading1("7. Repo Yap\u0131s\u0131 (\u00d6nerilen)"),
      body("Projenin klas\u00f6r yap\u0131s\u0131 a\u015fa\u011f\u0131daki gibi organize edilmeli:"),
      space(80),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [9026],
        rows: [
          new TableRow({ children: [new TableCell({
            shading: { fill: "1E293B", type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 200, right: 200 },
            width: { size: 9026, type: WidthType.DXA },
            borders: border("334155"),
            children: [new Paragraph({
              children: [new TextRun({ text: "  LibTracker/", font: "Consolas", size: 18, bold: true, color: "7C9EFF" })],
              spacing: { before: 0, after: 0 },
            })]
          })]})
        ].concat([
          ["  \u251c\u2500\u2500 backend/",            "7C9EFF"],
          ["  \u2502   \u251c\u2500\u2500 app.py",       "86EFAC"],
          ["  \u2502   \u251c\u2500\u2500 models.py",     "86EFAC"],
          ["  \u2502   \u251c\u2500\u2500 database.py    # Singleton SystemDatabase", "FDE68A"],
          ["  \u2502   \u251c\u2500\u2500 routes/",       "86EFAC"],
          ["  \u2502   \u2502   \u251c\u2500\u2500 auth.py",             "A5B4FC"],
          ["  \u2502   \u2502   \u251c\u2500\u2500 libraries.py",        "A5B4FC"],
          ["  \u2502   \u2502   \u251c\u2500\u2500 reservations.py",     "A5B4FC"],
          ["  \u2502   \u2502   \u2514\u2500\u2500 feedback.py",         "A5B4FC"],
          ["  \u2502   \u2514\u2500\u2500 requirements.txt",  "86EFAC"],
          ["  \u251c\u2500\u2500 frontend/",          "7C9EFF"],
          ["  \u2502   \u2514\u2500\u2500 demo.html",     "86EFAC"],
          ["  \u251c\u2500\u2500 tests/",             "7C9EFF"],
          ["  \u2502   \u251c\u2500\u2500 conftest.py",  "FCA5A5"],
          ["  \u2502   \u251c\u2500\u2500 test_auth.py",  "FCA5A5"],
          ["  \u2502   \u251c\u2500\u2500 test_reservations.py", "FCA5A5"],
          ["  \u2502   \u2514\u2500\u2500 test_feedback.py",    "FCA5A5"],
          ["  \u251c\u2500\u2500 Documentation/",     "7C9EFF"],
          ["  \u2514\u2500\u2500 README.md",          "86EFAC"],
        ].map(([line, color]) => new TableRow({ children: [new TableCell({
          shading: { fill: "0F172A", type: ShadingType.CLEAR },
          margins: { top: 20, bottom: 20, left: 200, right: 200 },
          width: { size: 9026, type: WidthType.DXA },
          borders: {
            top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            left: { style: BorderStyle.SINGLE, size: 4, color: "334155" },
            right: { style: BorderStyle.SINGLE, size: 4, color: "334155" },
          },
          children: [new Paragraph({
            children: [new TextRun({ text: line, font: "Consolas", size: 18, color })],
            spacing: { before: 0, after: 0 },
          })]
        })]}))),
      }),

      space(200),
      divider(),

      // ── FINAL NOTE ────────────────────────────────────────
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [9026],
        rows: [new TableRow({ children: [new TableCell({
          shading: { fill: DARK_BLUE, type: ShadingType.CLEAR },
          margins: { top: 200, bottom: 200, left: 300, right: 300 },
          width: { size: 9026, type: WidthType.DXA },
          borders: border(DARK_BLUE),
          children: [
            new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "\ud83c\udfc1 Ba\u015far\u0131lar Rebs Dev!", font: "Arial Black", size: 30, bold: true, color: "FFFFFF" })], spacing: { before: 0, after: 80 } }),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "LibTracker \u2013 \u00dcniversite \u00f6\u011frencilerinin zaman\u0131n\u0131 kurtaran sistem.", font: "Arial", size: 20, color: "AAB4D4" })], spacing: { before: 0, after: 0 } }),
          ]
        })]})],
      }),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:\\Users\\s.ketenoglu\\Desktop\\LibTracker\\Documentation\\TeamRebsDev_TaskAssignment_v2.docx", buffer);
  console.log("SUCCESS: TeamRebsDev_TaskAssignment.docx olusturuldu!");
}).catch(err => {
  console.error("ERROR:", err.message);
  process.exit(1);
});
