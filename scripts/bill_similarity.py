import os
import re
import json # Added for JSON output
from sentence_transformers import SentenceTransformer
import numpy as np # For type hinting embeddings if preferred
from sklearn.metrics.pairwise import cosine_similarity

# Global variable for the SBERT model and its name
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'
_sbert_model = None

def get_sbert_model() -> SentenceTransformer:
    """
    Loads and caches the SBERT model.

    Returns:
        The initialized SentenceTransformer model.
    
    Raises:
        RuntimeError: If the model fails to load.
    """
    global _sbert_model
    if _sbert_model is None:
        try:
            _sbert_model = SentenceTransformer(SBERT_MODEL_NAME)
            print(f"SBERT model '{SBERT_MODEL_NAME}' loaded successfully.")
        except Exception as e:
            print(f"Error loading SBERT model '{SBERT_MODEL_NAME}': {e}")
            # Depending on desired behavior, could raise an error or return None
            # For now, let's raise to make it clear if model loading fails.
            raise RuntimeError(f"Failed to load SBERT model: {e}") from e
    return _sbert_model

def generate_embeddings(text_segments: list[str]) -> list[list[float]]:
    """
    Generates SBERT embeddings for a list of text segments.

    Args:
        text_segments: A list of strings, where each string is a text segment.

    Returns:
        A list of embeddings, where each embedding is a list of floats.
        Returns an empty list if input is empty or model fails to load.
    
    Raises:
        ValueError: If text_segments is not a list of strings.
        RuntimeError: If the SBERT model cannot be obtained.
    """
    if not isinstance(text_segments, list) or not all(isinstance(seg, str) for seg in text_segments):
        raise ValueError("Input 'text_segments' must be a list of strings.")

    if not text_segments:
        return []

    try:
        model = get_sbert_model()
        if model is None: # Should be caught by get_sbert_model's raise, but as a safeguard.
             raise RuntimeError("SBERT model is not available.")
    except RuntimeError as e:
        print(f"Error obtaining SBERT model for embedding generation: {e}")
        # Or re-raise if critical: raise
        return [] # Return empty or handle as appropriate

    try:
        print(f"Generating embeddings for {len(text_segments)} segments...")
        # The encode method returns numpy arrays by default. Convert to list of lists of floats.
        embeddings_np = model.encode(text_segments, show_progress_bar=True)
        embeddings = [emb.tolist() for emb in embeddings_np]
        print("Embeddings generated successfully.")
        return embeddings
    except Exception as e:
        print(f"Error during embedding generation: {e}")
        return []


def load_bills(bill_sources: list[str]) -> list[str]:
    """
    Loads bill content from a list of sources.

    Each source can be a file path to a text file or the direct text of a bill.

    Args:
        bill_sources: A list of strings, where each string is either a
                      file path or the bill text itself.

    Returns:
        A list of strings, where each string is the content of a bill.
    """
    bill_contents = []
    for source in bill_sources:
        if os.path.exists(source):
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    bill_contents.append(f.read())
            except FileNotFoundError:
                print(f"Warning: File not found at {source}. Skipping.")
            except Exception as e:
                print(f"Warning: Error reading file {source}: {e}. Skipping.")
        else:
            # Assume it's direct text
            bill_contents.append(source)
    return bill_contents

def preprocess_text(text: str) -> str:
    """
    Performs basic cleaning of bill text.

    - Removes extra whitespace (leading/trailing, multiple spaces).
    - Placeholder for removing common legal boilerplate.

    Args:
        text: The bill text to preprocess.

    Returns:
        The cleaned bill text.
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # TODO: Consider removing common legal boilerplate if identifiable patterns emerge.
    return text

def segment_bill(bill_text: str, segment_size: int = 256, overlap: int = 64) -> list[str]:
    """
    Segments the bill text into smaller chunks based on word count.

    Args:
        bill_text: The text of the bill to segment.
        segment_size: The desired number of words in each chunk.
        overlap: The number of words that should overlap between
                 consecutive chunks.

    Returns:
        A list of text segments.
    
    Note:
        This is a basic segmentation strategy. It could be improved by
        segmenting based on natural boundaries like paragraphs or sections
        if the input format allows and more sophisticated tokenization
        (e.g., from a library like NLTK or spaCy) is used.
    """
    words = bill_text.split()
    segments = []
    
    if not words:
        return []

    start = 0
    while start < len(words):
        end = start + segment_size
        segment_words = words[start:end]
        segments.append(" ".join(segment_words))
        
        if end >= len(words):
            break
        
        start += (segment_size - overlap)
        # Ensure start doesn't go backwards if overlap is too large, though current logic prevents this.
        # Also, ensure we make progress. If segment_size - overlap <= 0, this would loop infinitely.
        if segment_size - overlap <= 0:
            # This case should ideally be prevented by input validation or better logic
            # For now, advance by at least one word to prevent infinite loop
            print("Warning: segment_size <= overlap, which may lead to issues. Advancing by 1 word.")
            start = end - segment_size + 1 


    return segments

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    
    # Create dummy bill files
    if not os.path.exists('dummy_bills'):
        os.makedirs('dummy_bills')
    
    bill1_content = """This is the first bill. It has several sentences.
    It talks about important matters for the nation. We need to ensure
    that all citizens are treated fairly under this new legislation.
    The economic impact will be significant but manageable.
    Further clauses will detail the implementation specifics.
    This bill aims to improve infrastructure and public services.
    It is a long document with many sections.
    """
    
    bill2_content = """This is bill number two. It focuses on environmental protection.
    We must act now to prevent further damage to our planet.
    This legislation introduces new regulations for industries.
    Renewable energy sources are heavily promoted.
    Carbon emissions must be reduced significantly by 2030.
    There are penalties for non-compliance.
    """

    bill3_direct_text = "This is the third bill, provided as direct text. It is shorter. It concerns space exploration and funding for new missions to Mars."

    with open('dummy_bills/bill1.txt', 'w') as f:
        f.write(bill1_content)
    with open('dummy_bills/bill2.txt', 'w') as f:
        f.write(bill2_content)

    bill_sources_list = [
        'dummy_bills/bill1.txt', 
        'dummy_bills/bill2.txt', 
        'non_existent_bill.txt', # Test FileNotFoundError
        bill3_direct_text
    ]

    print("--- Loading Bills ---")
    loaded_bill_texts = load_bills(bill_sources_list)
    for i, bill_t in enumerate(loaded_bill_texts):
        print(f"Bill {i+1} (first 100 chars): {bill_t[:100]}...")
    print(f"Total bills loaded: {len(loaded_bill_texts)}\n")

    if loaded_bill_texts:
        print("--- Preprocessing First Loaded Bill ---")
        first_bill_text = loaded_bill_texts[0]
        # Add some extra whitespace for testing preprocess_text
        first_bill_text_with_extra_space = "   " + first_bill_text.replace(". ", ".  ") + "   "
        preprocessed_bill = preprocess_text(first_bill_text_with_extra_space)
        print(f"Original (first 100 chars with extra space): {first_bill_text_with_extra_space[:120]}...")
        print(f"Preprocessed (first 100 chars): {preprocessed_bill[:100]}...\n")

        print("--- Segmenting First Preprocessed Bill ---")
        segments = segment_bill(preprocessed_bill, segment_size=30, overlap=10)
        print(f"Number of segments: {len(segments)}")
        for i, seg in enumerate(segments):
            print(f"Segment {i+1}: {seg}")
            if i == 2: # Print only a few segments
                print("...")
                break
        print("\n")

        print("--- Segmenting Short Bill (direct text) ---")
        short_bill_preprocessed = preprocess_text(loaded_bill_texts[-1]) # Last bill is the short one
        segments_short = segment_bill(short_bill_preprocessed, segment_size=10, overlap=3)
        print(f"Number of segments for short bill: {len(segments_short)}")
        for i, seg in enumerate(segments_short):
            print(f"Segment {i+1}: {seg}")

    # Clean up dummy files
    # os.remove('dummy_bills/bill1.txt')
    # os.remove('dummy_bills/bill2.txt')
    # os.rmdir('dummy_bills')
    # print("\nCleaned up dummy files.")
    print("\nNote: Dummy files not cleaned up automatically for inspection if needed.")
    print("Run 'rm -rf dummy_bills' to clean up if they were created.")


def calculate_similarity_scores(embeddings1: list[list[float]], embeddings2: list[list[float]] = None) -> list[tuple[int, int, float]]:
    """
    Calculates cosine similarity scores between embeddings.

    If only embeddings1 is provided, calculates similarity for all unique pairs within embeddings1.
    If embeddings1 and embeddings2 are provided, calculates similarity for all pairs between them.

    Args:
        embeddings1: A list of embeddings (each embedding is a list of floats).
        embeddings2: An optional second list of embeddings.

    Returns:
        A list of tuples, where each tuple is (index1, index2, score).
        index1 refers to an embedding in embeddings1.
        index2 refers to an embedding in embeddings2 (or embeddings1 if comparing within).
        score is their cosine similarity.
        Returns an empty list if input embeddings are invalid or empty.
    """
    if not embeddings1:
        return []

    # Convert to numpy arrays for cosine_similarity function
    np_embeddings1 = np.array(embeddings1)

    if embeddings2 is not None:
        if not embeddings2:
            return []
        np_embeddings2 = np.array(embeddings2)
        similarity_matrix = cosine_similarity(np_embeddings1, np_embeddings2)
        
        scores = []
        for i in range(similarity_matrix.shape[0]):
            for j in range(similarity_matrix.shape[1]):
                scores.append((i, j, similarity_matrix[i, j]))
        return scores
    else:
        # Intra-list comparison
        similarity_matrix = cosine_similarity(np_embeddings1)
        scores = []
        # Iterate over the upper triangle of the matrix to avoid self-comparison and duplicates
        for i in range(similarity_matrix.shape[0]):
            for j in range(i + 1, similarity_matrix.shape[1]): # j starts from i + 1
                scores.append((i, j, similarity_matrix[i, j]))
        return scores

def find_similar_segments(
    bill_id1: str,
    segments1: list[str],
    embeddings1: list[list[float]],
    bill_id2: str = None,
    segments2: list[str] = None,
    embeddings2: list[list[float]] = None,
    similarity_threshold: float = 0.8
) -> list[dict]:
    """
    Finds pairs of similar text segments based on a similarity threshold.

    Compares segments within a single bill if only bill1 data is provided,
    or between two bills if bill2 data is also provided.

    Args:
        bill_id1: Identifier for the first bill.
        segments1: List of text segments for the first bill.
        embeddings1: List of embeddings for the segments of the first bill.
        bill_id2: Optional identifier for the second bill.
        segments2: Optional list of text segments for the second bill.
        embeddings2: Optional list of embeddings for the segments of the second bill.
        similarity_threshold: The minimum cosine similarity score to consider
                              segments as similar.

    Returns:
        A list of dictionaries, each detailing a pair of similar segments.
        Each dictionary includes bill IDs, segment indices, segment texts,
        and the similarity score.
    """
    if bill_id2 is None or segments2 is None or embeddings2 is None:
        # Intra-bill comparison
        similarity_scores = calculate_similarity_scores(embeddings1)
        target_segments2 = segments1 # Compare within the same bill's segments
        target_bill_id2 = bill_id1
    else:
        # Inter-bill comparison
        similarity_scores = calculate_similarity_scores(embeddings1, embeddings2)
        target_segments2 = segments2
        target_bill_id2 = bill_id2

    similar_pairs = []
    for idx1, idx2, score in similarity_scores:
        if score >= similarity_threshold:
            try:
                pair_info = {
                    'bill1_id': bill_id1,
                    'segment1_index': idx1,
                    'segment1_text': segments1[idx1],
                    'bill2_id': target_bill_id2,
                    'segment2_index': idx2,
                    'segment2_text': target_segments2[idx2],
                    'similarity_score': score
                }
                similar_pairs.append(pair_info)
            except IndexError:
                print(f"Warning: IndexError while accessing segments. idx1={idx1}, len(segments1)={len(segments1)}, idx2={idx2}, len(target_segments2)={len(target_segments2)}. Skipping this pair.")
                continue
                
    return similar_pairs


if __name__ == '__main__':
    # Example Usage (for testing purposes)
    
    # Create dummy bill files
    if not os.path.exists('dummy_bills'):
        os.makedirs('dummy_bills')
    
    bill1_content = """This is the first bill. It has several sentences.
    It talks about important matters for the nation. We need to ensure
    that all citizens are treated fairly under this new legislation.
    The economic impact will be significant but manageable.
    Further clauses will detail the implementation specifics.
    This bill aims to improve infrastructure and public services.
    It is a long document with many sections.
    A very similar section about national infrastructure projects will appear later.
    This is for testing intra-bill similarity.
    National infrastructure projects are key to our growth.
    """
    
    bill2_content = """This is bill number two. It focuses on environmental protection.
    We must act now to prevent further damage to our planet.
    This legislation introduces new regulations for industries.
    Renewable energy sources are heavily promoted.
    Carbon emissions must be reduced significantly by 2030.
    There are penalties for non-compliance.
    Interestingly, this bill also mentions national infrastructure projects for green energy.
    """

    bill3_direct_text = "This is the third bill, provided as direct text. It is shorter. It concerns space exploration and funding for new missions to Mars."

    with open('dummy_bills/bill1.txt', 'w') as f:
        f.write(bill1_content)
    with open('dummy_bills/bill2.txt', 'w') as f:
        f.write(bill2_content)

    bill_sources_list = [
        'dummy_bills/bill1.txt', 
        'dummy_bills/bill2.txt', 
        'non_existent_bill.txt', # Test FileNotFoundError
        bill3_direct_text
    ]

    print("--- Loading Bills ---")
    loaded_bill_texts = load_bills(bill_sources_list)
    if len(loaded_bill_texts) < 2:
        print("Need at least two bills for full example. Exiting example.")
        # Clean up logic if needed
        exit()
        
    for i, bill_t in enumerate(loaded_bill_texts):
        print(f"Bill {i+1} (first 100 chars): {bill_t[:100]}...")
    print(f"Total bills loaded: {len(loaded_bill_texts)}\n")

    # Process first two loaded bills for similarity comparison
    bill1_id = "bill1.txt" # Assuming first loaded bill corresponds to this ID
    bill1_text = loaded_bill_texts[0]
    bill1_preprocessed = preprocess_text(bill1_text)
    bill1_segments = segment_bill(bill1_preprocessed, segment_size=20, overlap=5) # Smaller segments for more overlap chances
    
    bill2_id = "bill2.txt" # Assuming second loaded bill
    bill2_text = loaded_bill_texts[1]
    bill2_preprocessed = preprocess_text(bill2_text)
    bill2_segments = segment_bill(bill2_preprocessed, segment_size=20, overlap=5)

    print(f"\n--- Segments for {bill1_id} (first 3) ---")
    for i, seg in enumerate(bill1_segments[:3]): print(f" {i}: {seg}")
    print(f"\n--- Segments for {bill2_id} (first 3) ---")
    for i, seg in enumerate(bill2_segments[:3]): print(f" {i}: {seg}")


    # --- Example for Embedding Generation ---
    bill1_embeddings = []
    bill2_embeddings = []

    if bill1_segments:
        print(f"\n--- Generating Embeddings for {bill1_id} ---")
        try:
            bill1_embeddings = generate_embeddings(bill1_segments)
            if bill1_embeddings:
                print(f"Number of embeddings for {bill1_id}: {len(bill1_embeddings)}")
            else:
                print(f"No embeddings generated for {bill1_id}.")
        except RuntimeError as e:
            print(f"Could not generate embeddings for {bill1_id}: {e}")

    if bill2_segments:
        print(f"\n--- Generating Embeddings for {bill2_id} ---")
        try:
            bill2_embeddings = generate_embeddings(bill2_segments)
            if bill2_embeddings:
                print(f"Number of embeddings for {bill2_id}: {len(bill2_embeddings)}")
            else:
                print(f"No embeddings generated for {bill2_id}.")
        except RuntimeError as e:
            print(f"Could not generate embeddings for {bill2_id}: {e}")


    # --- Example for Similarity Calculation and Conflict/Overlap Detection ---
    if bill1_embeddings and bill1_segments:
        print(f"\n--- Finding Intra-Bill Similar Segments for {bill1_id} (Threshold: 0.7) ---")
        intra_bill_similarities = find_similar_segments(
            bill_id1=bill1_id,
            segments1=bill1_segments,
            embeddings1=bill1_embeddings,
            similarity_threshold=0.7 # Adjusted threshold for example
        )
        if intra_bill_similarities:
            print(f"Found {len(intra_bill_similarities)} intra-bill similar segment pairs in {bill1_id}:")
            for item in intra_bill_similarities:
                print(f"  Score: {item['similarity_score']:.4f}")
                print(f"  Segment {item['segment1_index']} ({item['bill1_id']}): '{item['segment1_text'][:50]}...'")
                print(f"  Segment {item['segment2_index']} ({item['bill2_id']}): '{item['segment2_text'][:50]}...'")
        else:
            print(f"No significant intra-bill similarities found in {bill1_id}.")

    if bill1_embeddings and bill2_embeddings and bill1_segments and bill2_segments:
        print(f"\n--- Finding Inter-Bill Similar Segments between {bill1_id} and {bill2_id} (Threshold: 0.6) ---")
        inter_bill_similarities = find_similar_segments(
            bill_id1=bill1_id,
            segments1=bill1_segments,
            embeddings1=bill1_embeddings,
            bill_id2=bill2_id,
            segments2=bill2_segments,
            embeddings2=bill2_embeddings,
            similarity_threshold=0.6 # Adjusted threshold for example
        )
        if inter_bill_similarities:
            print(f"Found {len(inter_bill_similarities)} inter-bill similar segment pairs between {bill1_id} and {bill2_id}:")
            for item in inter_bill_similarities:
                print(f"  Score: {item['similarity_score']:.4f}")
                print(f"  Segment {item['segment1_index']} ({item['bill1_id']}): '{item['segment1_text'][:50]}...'")
                print(f"  Segment {item['segment2_index']} ({item['bill2_id']}): '{item['segment2_text'][:50]}...'")
        else:
            print(f"No significant inter-bill similarities found between {bill1_id} and {bill2_id}.")


    print("\nNote: Dummy files not cleaned up automatically for inspection if needed.")
    print("Run 'rm -rf dummy_bills' to clean up if they were created.")


    # --- Example for Embedding Generation ---
    if loaded_bill_texts and segments: # Use segments from the first bill example
        print("\n--- Generating Embeddings for First Bill's Segments ---")
        # This block was part of the previous step's example. 
        # The new example for similarity is self-contained above using bill1_embeddings and bill2_embeddings.
        # To avoid confusion and re-running, this older example block for embedding generation
        # on 'segments' (which was from the very first bill only) can be considered redundant
        # if the new example structure for similarity (which re-processes bill1 and bill2) is preferred.
        # For now, it will run if `segments` is still in scope from that earlier part of `if __name__ == '__main__'`
        # but the more comprehensive similarity examples are above.
        pass # Keep this pass or remove the block if it's too confusing with the new example flow

    # --- Example for Reporting Similarities ---
    if intra_bill_similarities:
        print("\n--- Reporting Intra-Bill Similarities (Console) ---")
        report_similarities(intra_bill_similarities)

        print("\n--- Reporting Intra-Bill Similarities (JSON File) ---")
        report_similarities(intra_bill_similarities, output_file="intra_bill_similarity_report.json")

    if inter_bill_similarities:
        print("\n--- Reporting Inter-Bill Similarities (Console) ---")
        report_similarities(inter_bill_similarities)

        print("\n--- Reporting Inter-Bill Similarities (JSON File) ---")
        report_similarities(inter_bill_similarities, output_file="inter_bill_similarity_report.json")
        
        # Example of cleaning up the created JSON file if desired after inspection
        # if os.path.exists("intra_bill_similarity_report.json"):
        #     os.remove("intra_bill_similarity_report.json")
        # if os.path.exists("inter_bill_similarity_report.json"):
        #     os.remove("inter_bill_similarity_report.json")

def report_similarities(similarities: list[dict], output_file: str = None):
    """
    Reports similarity results either to the console or saves them to a JSON file.

    Args:
        similarities: A list of dictionaries, where each dictionary contains
                      details about a pair of similar segments. This is typically
                      the output from `find_similar_segments`.
        output_file: Optional. If provided, the similarities will be saved to this
                     JSON file. Otherwise, they will be printed to the console.
    """
    if not similarities:
        print("No similarities to report.")
        return

    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(similarities, f, indent=4, ensure_ascii=False)
            print(f"Similarity report saved to {output_file}")
        except IOError as e:
            print(f"Error saving report to {output_file}: {e}")
        except Exception as e: # Catch other potential errors during JSON writing
            print(f"An unexpected error occurred while writing to {output_file}: {e}")
    else:
        for item in similarities:
            print("Found potential similarity:")
            print(f"  Bill 1 ID: {item.get('bill1_id', 'N/A')}, Segment Index: {item.get('segment1_index', 'N/A')}")
            print(f"  Segment 1 Text: {item.get('segment1_text', 'N/A')}")
            print(f"  Bill 2 ID: {item.get('bill2_id', 'N/A')}, Segment Index: {item.get('segment2_index', 'N/A')}")
            print(f"  Segment 2 Text: {item.get('segment2_text', 'N/A')}")
            print(f"  Similarity Score: {item.get('similarity_score', 'N/A'):.4f}")
            print("---")

