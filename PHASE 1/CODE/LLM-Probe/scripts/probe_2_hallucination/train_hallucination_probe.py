import os
import sys
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.exceptions import UndefinedMetricWarning

# Include parent workspace folder in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer
from llm_probe.core.activations import extract_activations
from llm_probe.core.layer_selection import rank_layers, plot_layer_rankings
from llm_probe.core.probe import train_probe, evaluate_probe, save_probe

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHECKPOINT_PATH = "data/hallucination/labeled/activations_checkpoint.pkl"
RESULTS_DIR = "results/hallucination"
DATASET_PATH = "data/hallucination/labeled/dataset.parquet"

def main():
    logger.info("=== Starting Hallucination Probe Training Pipeline ===")
    
    # 1. Load labeled dataset
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset parquet file not found at: {DATASET_PATH}")
        sys.exit(1)
        
    df = pd.read_parquet(DATASET_PATH)
    logger.info(f"Loaded {len(df)} examples from {DATASET_PATH}")
    
    # Convert labels to binary (1 for hallucinated, 0 for grounded)
    labels = np.where(df['label'] == 'hallucinated', 1, 0)
    logger.info(f"Class distribution: {np.sum(labels == 1)} hallucinated (1), {np.sum(labels == 0)} grounded (0)")
    
    # 2. Checkpoint-Resumable Activation Extraction
    activations_dict = {}
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'rb') as f:
                activations_dict = pickle.load(f)
            logger.info(f"Loaded {len(activations_dict)} cached example activations from checkpoint.")
        except Exception as e:
            logger.warning(f"Could not load activations checkpoint: {e}. Starting fresh.")
            
    # Filter dataset items to identify which questions need forward passes
    unprocessed_questions = []
    unprocessed_rows = []
    for idx, row in df.iterrows():
        q = row['question']
        if q not in activations_dict:
            unprocessed_questions.append(q)
            unprocessed_rows.append(row)
            
    if unprocessed_questions:
        logger.info(f"Need to extract activations for {len(unprocessed_questions)} unprocessed examples.")
        logger.info(f"Loading model '{MODEL_NAME}' on '{DEVICE}'...")
        tokenizer = load_tokenizer(MODEL_NAME)
        model = load_model(MODEL_NAME, DEVICE)
        
        try:
            for i, row in enumerate(tqdm(unprocessed_rows, desc="Extracting activations")):
                q = row['question']
                ans = row['generated_answer']
                
                # Check for empty answers
                if not isinstance(ans, str) or not ans.strip():
                    logger.warning(f"Skipping question with empty generated answer: '{q}'")
                    continue
                    
                try:
                    acts = extract_activations(q, ans, model, tokenizer)
                    activations_dict[q] = acts
                except Exception as ex:
                    logger.error(f"Failed to extract activations for question: '{q}'. Error: {ex}")
                    
                # Periodically save checkpoint
                if (i + 1) % 50 == 0:
                    with open(CHECKPOINT_PATH, 'wb') as f:
                        pickle.dump(activations_dict, f)
                    logger.info(f"Saved checkpoint with {len(activations_dict)} examples to disk.")
                    
        except KeyboardInterrupt:
            logger.warning("Extraction process interrupted. Saving checkpoint to disk before exiting...")
            with open(CHECKPOINT_PATH, 'wb') as f:
                pickle.dump(activations_dict, f)
            logger.info("Checkpoint saved. Exiting.")
            sys.exit(0)
            
        # Final save of checkpoint
        with open(CHECKPOINT_PATH, 'wb') as f:
            pickle.dump(activations_dict, f)
        logger.info(f"Finished extraction. Saved {len(activations_dict)} total examples to checkpoint.")
    else:
        logger.info("All examples are already processed and cached. Skipping forward passes.")
        
    # Remove any rows from df that didn't end up with cached activations (e.g. failures or empty skips)
    valid_indices = []
    valid_labels = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        q = row['question']
        if q in activations_dict:
            valid_indices.append(idx)
            valid_labels.append(labels[idx])
            valid_rows.append(row)
            
    df = pd.DataFrame(valid_rows).reset_index(drop=True)
    labels = np.array(valid_labels)
    num_examples = len(df)
    
    if num_examples == 0:
        logger.error("No valid examples with activations are available. Exiting.")
        sys.exit(1)
        
    # 3. Compile activations by layer
    sample_q = df['question'].iloc[0]
    num_layers = len(activations_dict[sample_q])
    hidden_dim = activations_dict[sample_q][0]['last_token'].shape[0]
    
    last_token_by_layer = {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in range(num_layers)}
    mean_pooled_by_layer = {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in range(num_layers)}
    
    logger.info("Compiling activation feature matrices...")
    for idx, row in df.iterrows():
        q = row['question']
        example_acts = activations_dict[q]
        for l in range(num_layers):
            last_token_by_layer[l][idx] = example_acts[l]['last_token'].astype(np.float32)
            mean_pooled_by_layer[l][idx] = example_acts[l]['mean_pooled'].astype(np.float32)
            
    # 4. Stratified train/test split (80/20)
    # The split MUST happen before layer selection so that test-set labels and
    # activations cannot influence which layers or representation type is chosen.
    indices = np.arange(num_examples)
    train_idx, test_idx, y_train, y_test = train_test_split(
        indices, labels, test_size=0.2, stratify=labels, random_state=42
    )
    logger.info(f"Split: {len(train_idx)} train / {len(test_idx)} test examples "
                f"(stratified 80/20, random_state=42, "
                f"{np.sum(y_train==1)} hallucinated in train / {np.sum(y_test==1)} hallucinated in test)")

    # 5. Rank layers using Cohen's d on TRAINING DATA ONLY
    # Slicing layer dicts to train_idx ensures test-set labels and activations
    # have zero influence on layer selection or representation selection.
    logger.info("Ranking layers via absolute Cohen's d effect sizes (training data only)...")
    train_last = {l: last_token_by_layer[l][train_idx] for l in range(num_layers)}
    train_mean = {l: mean_pooled_by_layer[l][train_idx] for l in range(num_layers)}

    rankings_last = rank_layers(train_last, y_train)
    rankings_mean = rank_layers(train_mean, y_train)

    logger.info("=== Top 5 Layers for last-token representation ===")
    for rank_idx, (layer_idx, score) in enumerate(rankings_last[:5]):
        logger.info(f"  Rank {rank_idx+1}: Layer {layer_idx} (d={score:.4f})")

    logger.info("=== Top 5 Layers for mean-pooled representation ===")
    for rank_idx, (layer_idx, score) in enumerate(rankings_mean[:5]):
        logger.info(f"  Rank {rank_idx+1}: Layer {layer_idx} (d={score:.4f})")

    # Decide best representation type using training-only rankings
    best_last_score = rankings_last[0][1]
    best_mean_score = rankings_mean[0][1]

    if best_last_score >= best_mean_score:
        best_rep = 'last_token'
        best_rankings = rankings_last
        best_layer_data = last_token_by_layer
        logger.info(f"Selecting 'last_token' representation (highest Cohen's d = {best_last_score:.4f} at Layer {rankings_last[0][0]})")
    else:
        best_rep = 'mean_pooled'
        best_rankings = rankings_mean
        best_layer_data = mean_pooled_by_layer
        logger.info(f"Selecting 'mean_pooled' representation (highest Cohen's d = {best_mean_score:.4f} at Layer {rankings_mean[0][0]})")

    # Save the layer rankings chart (based on training-only Cohen's d)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    chart_path = os.path.join(RESULTS_DIR, "layer_rankings.png")
    plot_layer_rankings(best_rankings, chart_path)
    logger.info(f"Saved Cohen's d bar chart plot to: {chart_path}")

    # Select top 3 layers for probe feature concatenation
    selected_layers = [item[0] for item in best_rankings[:3]]
    logger.info(f"Concatenating features from top 3 layers: {selected_layers}")
    
    def prepare_features(layer_data, layers, target_indices):
        features = []
        for idx in target_indices:
            ex_feat = []
            for l in layers:
                ex_feat.append(layer_data[l][idx])
            features.append(np.concatenate(ex_feat))
        return np.array(features)
        
    X_train = prepare_features(best_layer_data, selected_layers, train_idx)
    X_test = prepare_features(best_layer_data, selected_layers, test_idx)
    
    # Feature Standardization (StandardScaler fitted on train split only)
    logger.info("Standardizing concatenated layer features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 6. Train the probe
    logger.info("Training Logistic Regression probe on scaled features...")
    probe = train_probe(X_train_scaled, y_train, use_mlp=False)
    
    # Evaluate
    metrics = evaluate_probe(probe, X_test_scaled, y_test)
    logger.info("=== Standard Probe Evaluation (80/20 Split, Scaled) ===")
    logger.info(f"Accuracy : {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall   : {metrics['recall']:.4f}")
    logger.info(f"F1 Score : {metrics['f1']:.4f}")
    logger.info("\nClassification Report:\n" + metrics['report'])
    logger.info("\nConfusion Matrix:\n" + str(metrics['confusion_matrix']))
    
    # Save the probe model & scaler dictionary
    probe_path = os.path.join(RESULTS_DIR, "probe.joblib")
    probe_dict = {
        'probe': probe,
        'scaler': scaler,
        'selected_layers': selected_layers,
        'representation_type': best_rep
    }
    save_probe(probe_dict, probe_path)
    logger.info(f"Saved trained probe and scaler payload dictionary to: {probe_path}")
    
    # Optional MLP training validation (on scaled features)
    logger.info("Training validation MLP probe on scaled features...")
    mlp_probe = train_probe(X_train_scaled, y_train, use_mlp=True)
    mlp_metrics = evaluate_probe(mlp_probe, X_test_scaled, y_test)
    logger.info("=== MLP Probe Evaluation (Scaled) ===")
    logger.info(f"MLP F1 Score: {mlp_metrics['f1']:.4f}")
    
    # 7. Generalization tests: hold out 'Misconceptions' and separately 'Law'
    gen_results = {}
    for holdout_cat in ['Misconceptions', 'Law']:
        logger.info(f"=== Running Held-Out Category Generalization Test (Holding out '{holdout_cat}') ===")
        
        train_gen_idx = np.where(df['category'] != holdout_cat)[0]
        test_gen_idx = np.where(df['category'] == holdout_cat)[0]
        
        logger.info(f"Training on: {len(train_gen_idx)} examples ({np.sum(labels[train_gen_idx] == 1)} hallucinated)")
        logger.info(f"Testing on : {len(test_gen_idx)} examples ({np.sum(labels[test_gen_idx] == 1)} hallucinated)")
        
        if len(test_gen_idx) == 0:
            logger.warning(f"No examples found for category '{holdout_cat}'. Skipping generalization test.")
            continue
            
        # FRESH layer / representation selection using OOD training data ONLY.
        # The held-out category is completely excluded from layer selection,
        # representation selection, scaler fitting, and probe training — it is
        # used only for final evaluation.
        y_gen_train = labels[train_gen_idx]
        y_gen_test  = labels[test_gen_idx]

        logger.info(f"OOD '{holdout_cat}': ranking layers on training data only ({holdout_cat} excluded from all decisions)...")
        ood_last = {l: last_token_by_layer[l][train_gen_idx] for l in range(num_layers)}
        ood_mean = {l: mean_pooled_by_layer[l][train_gen_idx] for l in range(num_layers)}

        ood_rl = rank_layers(ood_last, y_gen_train)
        ood_rm = rank_layers(ood_mean, y_gen_train)

        ood_ls = ood_rl[0][1]
        ood_ms = ood_rm[0][1]
        if ood_ls >= ood_ms:
            ood_rep = 'last_token'
            ood_rankings = ood_rl
            ood_ld = last_token_by_layer
        else:
            ood_rep = 'mean_pooled'
            ood_rankings = ood_rm
            ood_ld = mean_pooled_by_layer

        ood_layers = [item[0] for item in ood_rankings[:3]]
        logger.info(f"OOD '{holdout_cat}' selected layers: {ood_layers} (representation: {ood_rep})")

        X_gen_train = prepare_features(ood_ld, ood_layers, train_gen_idx)
        X_gen_test  = prepare_features(ood_ld, ood_layers, test_gen_idx)

        # Fit scaler on OOD generalization training set ONLY
        gen_scaler = StandardScaler()
        X_gen_train_scaled = gen_scaler.fit_transform(X_gen_train)
        X_gen_test_scaled  = gen_scaler.transform(X_gen_test)

        # Train and evaluate Linear Probe
        gen_probe = train_probe(X_gen_train_scaled, y_gen_train, use_mlp=False)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", category=UndefinedMetricWarning)
            res = evaluate_probe(gen_probe, X_gen_test_scaled, y_gen_test)
            
            # Check for precision undefined warning
            precision_undefined = False
            for warning in w:
                if "precision" in str(warning.message).lower() or "f-score is ill-defined" in str(warning.message).lower():
                    precision_undefined = True
                    
            cm = res['confusion_matrix']
            total_pos_preds = cm[0, 1] + cm[1, 1]
            
            gen_results[holdout_cat] = {
                'metrics': res,
                'pos_preds': total_pos_preds,
                'prec_undefined': precision_undefined
            }
            
            logger.info(f"Generalization '{holdout_cat}' F1 Score: {res['f1']:.4f}")
            logger.info(f"Generalization Confusion Matrix:\n{cm}")
            
    # 8. Save report file
    report_path = os.path.join(RESULTS_DIR, "probe_training_report.md")
    report_content = [
        "# Hallucination Probe Training & Evaluation Report\n",
        f"- **Best Representation**: `{best_rep}`",
        f"- **Best Layers (Cohen's d Rankings)**: `{[item[0] for item in best_rankings[:5]]}`",
        f"- **Selected Probe Layers (Top 3)**: `{selected_layers}`\n",
        "## In-Domain Evaluation (80/20 Stratified Split)",
        f"- **Accuracy**: `{metrics['accuracy']:.4f}`",
        f"- **Precision**: `{metrics['precision']:.4f}`",
        f"- **Recall**: `{metrics['recall']:.4f}`",
        f"- **F1 Score**: `{metrics['f1']:.4f}`",
        f"- **MLP Validation F1**: `{mlp_metrics['f1']:.4f}`\n",
        "### Confusion Matrix (Linear):",
        "```",
        str(metrics['confusion_matrix']),
        "```\n",
        "### Classification Report (Linear):",
        "```",
        metrics['report'],
        "```\n",
        "## Held-Out Category Generalization Tests\n"
    ]
    
    for holdout_cat, res in gen_results.items():
        m = res['metrics']
        prec_str = "UNDEFINED" if res['prec_undefined'] else f"{m['precision']:.4f}"
        report_content.extend([
            f"### Hold-Out Category: `{holdout_cat}`",
            f"- **Generalization F1**: `{m['f1']:.4f}`",
            f"- **Generalization Accuracy**: `{m['accuracy']:.4f}`",
            f"- **Generalization Precision**: `{prec_str}`",
            f"- **Generalization Recall**: `{m['recall']:.4f}`",
            f"- **Positive Predictions Made**: `{res['pos_preds']}`\n",
            "#### Confusion Matrix:",
            "```",
            str(m['confusion_matrix']),
            "```",
            "```",
            m['report'],
            "```\n"
        ])
        
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_content))
    logger.info(f"Full training report saved to: {report_path}")
    
    # 9. Summary block printed to console
    print("\n" + "="*50)
    print(" HALLUCINATION PROBE TRAINING SUMMARY")
    print("="*50)
    print(f"Best Representation: {best_rep}")
    print(f"Best Layer index   : {best_rankings[0][0]} (d={best_rankings[0][1]:.4f})")
    print(f"Selected Layers    : {selected_layers}")
    print(f"In-domain F1       : {metrics['f1']:.4f}")
    print(f"MLP Validation F1  : {mlp_metrics['f1']:.4f}")
    print("-"*50)
    for holdout_cat, res in gen_results.items():
        m = res['metrics']
        print(f"Held-out '{holdout_cat}' F1: {m['f1']:.4f} (Accuracy: {m['accuracy']:.4f})")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
