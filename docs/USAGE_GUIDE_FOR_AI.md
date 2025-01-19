# AI_USAGE_GUIDE

This file provides specific instructions for using the ai system with focus on LSTM modeling and its applications. Use this guide to explore and apply the system's features securely.

## LSTM System Overview

The LSTM system is integral to congressional workflow testing and automated learning tasks, including:

- Using the Congress.gov API to fetch data on Bills.
- Preprocessing data using design and categorical transforms.
- Training an LSTM model to predict bill progression.
- Automating workflows to retrain and evaluate the model, updating it when necessary.
- Saving the model and data for interactive analysis.

## Step-By-Step Implementation

Following step-by-step concepts, the system can:
 1. Collect data using the api.
 2. Preprocess and export the data to the *data/* directory.
 3. Setup training parameters, define the model, and validate.
 4. Run and monitor results automatically using GitHub workflows.
 5. Save trained models and generate visualizations for validation.
