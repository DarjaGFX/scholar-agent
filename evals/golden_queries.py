# evals/golden_queries.py
# Eval queries with expected researchers.
#
# GROUND-TRUTH RULE: every name below is a HUMAN-LABELED `human` from
# tests/data/golden_authors.csv — independent of the retrieval pipeline.
# Never fill `expected` from the system's own output (circularity: the eval
# would then measure the system against itself).
#
# NOTE: expected sets are NOT exhaustive. A returned researcher who is real
# but absent from a set counts as a miss, so precision@5 is a LOWER BOUND.

GOLDEN_QUERIES = [
    # --- the three labeled topics: full human sets from the golden set ---
    {"query": "retrieval augmented generation",
     "expected": {"Philip S. Yu", "Ji-Rong Wen", "Tat‐Seng Chua", "Zhicheng Dou",
                  "Maarten de Rijke", "Murali Krishna Pasupuleti",
                  "Franck Dernoncourt", "Wayne Xin Zhao", "Yang Liu",
                  "Julian McAuley"}},
    {"query": "machine translation",
     "expected": {"Graham Neubig", "Andy Way", "Hermann Ney", "Eiichiro Sumita",
                  "Pushpak Bhattacharyya", "Philipp Koehn", "Iryna Gurevych",
                  "Maosong Sun", "Preslav Nakov", "Furu Wei", "Dacheng Tao",
                  "Mohit Bansal", "Lucia Specia"}},
    {"query": "protein structure prediction",
     "expected": {"David Baker", "Nikos C. Kyrpides", "Vladimir N. Uversky",
                  "Eugene V. Koonin", "Tanja Woyke", "Natalia Ivanova",
                  "Henrik Zetterberg", "Jianlin Cheng", "Jens Meiler",
                  "Yang Zhang", "Bernhard Ø. Palsson", "Bernard Henrissat",
                  "Burkhard Rost", "Igor V. Grigoriev", "Kaj Blennow"}},
    # --- derived from the same labels: these authors' actual home fields ---
    {"query": "microbial genomics",
     "expected": {"Eugene V. Koonin", "Nikos C. Kyrpides", "Tanja Woyke",
                  "Natalia Ivanova", "Igor V. Grigoriev"}},
    {"query": "low-resource NLP",
     "expected": {"Graham Neubig", "Iryna Gurevych", "Preslav Nakov"}},
]
