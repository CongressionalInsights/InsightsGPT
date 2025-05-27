import argparse
import re
import json
import logging
from difflib import unified_diff

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Common legal boilerplate patterns to strip; extend as needed
BOILERPLATE_PATTERNS = [
    r"IN THE (SENATE|HOUSE) OF THE UNITED STATES.*?;",
    r"Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled:",
    r"Section \d+(?:\.\d+)*",
]

# Preprocess text: lowercase, remove boilerplate, normalize whitespace
def preprocess_text(text: str) -> str:
    # Remove boilerplate
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE | re.DOTALL)
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r"\s+", ' ', text).strip()
    return text

# Segment text into chunks based on paragraphs or fixed size
def segment_bill(text: str, segment_size: int = 100, overlap: int = 20) -> list:
    # First attempt paragraph-based segmentation
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    segments = []
    for para in paragraphs:
        words = para.split()
        if len(words) <= segment_size:
            segments.append(' '.join(words))
        else:
            # Fallback to sliding window
            for i in range(0, len(words), segment_size - overlap):
                chunk = words[i:i + segment_size]
                if chunk:
                    segments.append(' '.join(chunk))
    # Comment: basic segmentation; could improve by parsing semantic boundaries (sections, subsections)
    return segments

# Find similar segments with embeddings or fallback to TF-IDF
def find_similar_segments(segs1: list, segs2: list, threshold: float = 0.8) -> list:
    results = []

    # Use sentence-transformers if available
    if SentenceTransformer and util:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        emb1 = model.encode(segs1, convert_to_tensor=True)
        emb2 = model.encode(segs2, convert_to_tensor=True)
        sim_matrix = util.cos_sim(emb1, emb2)

        for i, row in enumerate(sim_matrix):
            for j, score in enumerate(row):
                if score >= threshold:
                    text1, text2 = segs1[i], segs2[j]
                    # Generate diff for detailed comparison
                    diff = '\n'.join(unified_diff(text1.split(), text2.split(), lineterm=''))
                    results.append({
                        'segment1_index': i,
                        'segment2_index': j,
                        'score': float(score),
                        'text1': text1,
                        'text2': text2,
                        'diff': diff
                    })
    else:
        logging.warning("sentence-transformers not installed; TF-IDF fallback not implemented.")
        # TODO: Implement TF-IDF based similarity as fallback
    return results

def main():
    parser = argparse.ArgumentParser(description='Compare two legislative texts for similarity, conflicts, and amendments.')
    parser.add_argument('--bill1', type=str, required=True, help='Path to first bill text file')
    parser.add_argument('--bill2', type=str, required=True, help='Path to second bill text file')
    parser.add_argument('--threshold', type=float, default=0.8, help='Similarity threshold (0-1)')
    parser.add_argument('--segment_size', type=int, default=100, help='Number of words per segment')
    parser.add_argument('--overlap', type=int, default=20, help='Number of overlapping words between segments')
    parser.add_argument('--output', type=str, help='Optional JSON file to write results')
    args = parser.parse_args()

    # Read files
    with open(args.bill1, 'r', encoding='utf-8') as f:
        raw1 = f.read()
    with open(args.bill2, 'r', encoding='utf-8') as f:
        raw2 = f.read()

    # Preprocess
    proc1 = preprocess_text(raw1)
    proc2 = preprocess_text(raw2)

    # Segment
    segs1 = segment_bill(proc1, args.segment_size, args.overlap)
    segs2 = segment_bill(proc2, args.segment_size, args.overlap)

    # Find similarities
    matches = find_similar_segments(segs1, segs2, args.threshold)

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            json.dump(matches, out, indent=2)
        logging.info(f"Results written to {args.output}")
    else:
        print(json.dumps(matches, indent=2))

if __name__ == '__main__':
    main()
