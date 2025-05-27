# Models Overview

This directory contains files and documents related to the modeling efforts within the project. This includes traditional machine learning models and potentially deep learning approaches.

## LSTM Modeling
The project involves LSTM (Long Short-Term Memory) modeling, likely for sequence-based data such as time series or textual analysis.

Suggested repository structure for LSTM related work:

 - `data/`: Datasets for training and validation specific to LSTM models.
 - `notebooks/`: Experimental notebooks with examples or explanations for LSTM development.
 - `models/`: Storage for trained LSTM models and associated artifacts.
 - `scripts/lstm_implementation.py`: Scripts related to LSTM model training, evaluation, or deployment. (Assuming `lstm_implementation.on` was a typo for `.py`)

## Semantic Similarity Models
The project also leverages pre-trained sentence embedding models (e.g., SBERT via the `sentence-transformers` library) for semantic textual similarity tasks, such as identifying overlaps in legislative documents. Implementations related to this can be found in the `scripts/` directory (e.g., `bill_similarity.py`). These models are typically loaded on-the-fly by the scripts rather than being stored directly in this `models/` directory, unless fine-tuning is performed.
