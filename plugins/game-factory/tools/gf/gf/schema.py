"""Production file headings and table layouts the CLI reads and writes.

Everything the CLI parses out of production/*.md lives here, so the producer
skill and the templates can match it. Change a value here and in the README.
"""

# production/STATE.md: lines of the form "<field>: <value>".
STATE_FIELDS = ("Current wave", "Next step")

# production/ASSETS.md: one table, these columns in this order.
ASSET_HEADERS = ["asset_id", "type", "file", "model", "task_id", "refs", "credits", "status", "wave"]

# production/BUDGET.md: rows appended as
# "| <wave> | <balance before> | up to <cap> | <spent> | <balance after> | <notes> |".
BUDGET_HEADERS = ["wave", "balance_before", "cap", "spent", "balance_after", "notes"]
BUDGET_CAP_PREFIX = "up to"

# Status or file words that make an ASSETS.md row skip the file-exists check.
SKIP_STATUS_WORDS = ("planned", "pending", "rejected", "to generate", "do not generate", "no generation")

# docs/05-script/expressions.md: first cell of the header row, and the marker
# in the "cell" column that sends the lookup to the character sheet.
EXPRESSIONS_HEADERS = ["chr_id", "Expression", "Lines", "Description", "Cell"]
SEE_SHEET = "see sheet"

# ID prefixes the continuity check recognises.
ID_PREFIXES = ("chr_", "npc_", "en_", "boss_", "loc_", "seq_", "ill_", "prop_", "plx_", "sb_")

# Dialogue line format in docs/05-script/chNN.md:
#   SPEAKER [optional note] (expression): text
MAX_LINE_CHARS = 80

# Folder names that mark non-final art (matched by the "assets" excludes in gf.json too).
REJECTED_DIR = "_rejected"
REFS_DIR = "_refs"
LEGACY_DIR = "_legacy"
