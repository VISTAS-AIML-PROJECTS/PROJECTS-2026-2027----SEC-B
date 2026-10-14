import os
import sys
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import UndefinedMetricWarning

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Include parent folder in path to import llm_probe
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm_probe.config import MODEL_NAME, DEVICE
from llm_probe.models.loader import load_model, load_tokenizer
from llm_probe.core.activations import extract_activations
from llm_probe.core.layer_selection import rank_layers, plot_layer_rankings
from llm_probe.core.probe import train_probe, evaluate_probe, save_probe

CHECKPOINT_PATH = "data/memorization/labeled/activations_checkpoint.pkl"
RESULTS_DIR = "results/memorization"

def main():
    logger.info("=== Starting Memorization Probe Training Pipeline ===")
    
    # 1. Load labeled dataset
    dataset_path = "data/memorization/labeled/dataset.parquet"
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset parquet file not found at: {dataset_path}")
        sys.exit(1)
        
    df = pd.read_parquet(dataset_path)
    logger.info(f"Loaded {len(df)} examples from {dataset_path}")
    
    # Convert labels to binary (1 for memorized, 0 for novel)
    labels = np.where(df['label'] == 'memorized', 1, 0)
    logger.info(f"Class distribution: {np.sum(labels == 1)} memorized, {np.sum(labels == 0)} novel")
    
    # 2. Checkpoint-Resumable Activation Extraction
    activations_dict = {}
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'rb') as f:
                activations_dict = pickle.load(f)
            logger.info(f"Loaded {len(activations_dict)} cached example activations from checkpoint.")
        except Exception as e:
            logger.warning(f"Failed to load checkpoint file ({e}). Starting extraction from scratch.")
            
    # Check if there are missing activations
    missing_indices = []
    for idx, row in df.iterrows():
        sid = row['source_id']
        if sid not in activations_dict:
            missing_indices.append(idx)
            
    if missing_indices:
        logger.info(f"Extracting activations for {len(missing_indices)} missing examples on {DEVICE}...")
        model = load_model(MODEL_NAME, DEVICE)
        tokenizer = load_tokenizer(MODEL_NAME)
        
        extracted_count = 0
        try:
            for idx in tqdm(missing_indices, desc="Extracting activations"):
                row = df.iloc[idx]
                sid = row['source_id']
                prompt = row['prompt']
                gen = row['generated_continuation']
                
                # Run forward pass to extract hidden states
                try:
                    example_acts = extract_activations(prompt, gen, model, tokenizer)
                    
                    # Convert to float16 to optimize storage space
                    example_acts_f16 = {}
                    for l_idx, rep in example_acts.items():
                        example_acts_f16[l_idx] = {
                            'last_token': rep['last_token'].astype(np.float16),
                            'mean_pooled': rep['mean_pooled'].astype(np.float16)
                        }
                    activations_dict[sid] = example_acts_f16
                    extracted_count += 1
                except Exception as e:
                    logger.error(f"Error extracting activations for {sid}: {e}")
                    continue
                    
                # Incrementally save every 50 runs
                if extracted_count % 50 == 0:
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
        
    # 3. Compile activations by layer
    num_examples = len(df)
    sample_sid = df['source_id'].iloc[0]
    num_layers = len(activations_dict[sample_sid])
    hidden_dim = activations_dict[sample_sid][0]['last_token'].shape[0]
    
    last_token_by_layer = {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in range(num_layers)}
    mean_pooled_by_layer = {l: np.zeros((num_examples, hidden_dim), dtype=np.float32) for l in range(num_layers)}
    
    logger.info("Compiling activation feature matrices...")
    for idx, row in df.iterrows():
        sid = row['source_id']
        if sid not in activations_dict:
            continue
        example_acts = activations_dict[sid]
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
                f"{np.sum(y_train==1)} memorized in train / {np.sum(y_test==1)} memorized in test)")

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
    
    # 7. Held-Out Category Generalization Test (Excluding code_snippets)
    logger.info("=== Running Held-Out Category Generalization Test (Holding out code_snippets) ===")
    
    train_gen_idx = np.where(df['source_category'] != 'code_snippets')[0]
    test_gen_idx  = np.where(df['source_category'] == 'code_snippets')[0]

    logger.info(f"OOD training on: {len(train_gen_idx)} non-code examples ({np.sum(labels[train_gen_idx] == 1)} memorized)")
    logger.info(f"OOD testing on : {len(test_gen_idx)} code examples ({np.sum(labels[test_gen_idx] == 1)} memorized)")

    # FRESH layer / representation selection using OOD training data ONLY.
    # code_snippets is completely excluded from layer selection, representation
    # selection, scaler fitting, and probe training — it is used only for
    # final evaluation.
    y_gen_train = labels[train_gen_idx]
    y_gen_test  = labels[test_gen_idx]

    logger.info("OOD: ranking layers on non-code training data only (code_snippets excluded from all decisions)...")
    ood_last = {l: last_token_by_layer[l][train_gen_idx] for l in range(num_layers)}
    ood_mean = {l: mean_pooled_by_layer[l][train_gen_idx] for l in range(num_layers)}

    ood_rankings_last = rank_layers(ood_last, y_gen_train)
    ood_rankings_mean = rank_layers(ood_mean, y_gen_train)

    ood_best_last_score = ood_rankings_last[0][1]
    ood_best_mean_score = ood_rankings_mean[0][1]
    if ood_best_last_score >= ood_best_mean_score:
        ood_best_rep = 'last_token'
        ood_best_rankings = ood_rankings_last
        ood_layer_data = last_token_by_layer
        logger.info(f"OOD: selecting 'last_token' representation (d={ood_best_last_score:.4f})")
    else:
        ood_best_rep = 'mean_pooled'
        ood_best_rankings = ood_rankings_mean
        ood_layer_data = mean_pooled_by_layer
        logger.info(f"OOD: selecting 'mean_pooled' representation (d={ood_best_mean_score:.4f})")

    ood_selected_layers = [item[0] for item in ood_best_rankings[:3]]
    logger.info(f"OOD selected layers: {ood_selected_layers} (representation: {ood_best_rep})")

    X_gen_train = prepare_features(ood_layer_data, ood_selected_layers, train_gen_idx)
    X_gen_test  = prepare_features(ood_layer_data, ood_selected_layers, test_gen_idx)

    # Fit scaler on OOD generalization training set ONLY
    gen_scaler = StandardScaler()
    X_gen_train_scaled = gen_scaler.fit_transform(X_gen_train)
    X_gen_test_scaled  = gen_scaler.transform(X_gen_test)
    
    # Train and evaluate Linear Probe
    logger.info("Training Linear Probe on Generalization split...")
    gen_probe = train_probe(X_gen_train_scaled, y_gen_train, use_mlp=False)
    
    # Helper to check if precision is technically undefined
    def get_metrics_and_check_warning(model, X_val, y_val, name="Linear Probe"):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", category=UndefinedMetricWarning)
            res = evaluate_probe(model, X_val, y_val)
            
            # Check if any UndefinedMetricWarning was raised for precision
            precision_undefined = False
            for warning in w:
                if "precision" in str(warning.message).lower() or "f-score is ill-defined" in str(warning.message).lower():
                    precision_undefined = True
                    
            cm = res['confusion_matrix']
            total_pos_preds = cm[0, 1] + cm[1, 1] # FP + TP
            
            if total_pos_preds == 0:
                logger.warning(f"[{name}] Warning: Model made ZERO positive predictions. Precision is mathematically UNDEFINED.")
            else:
                logger.info(f"[{name}] Model made {total_pos_preds} positive predictions (TP={cm[1, 1]}, FP={cm[0, 1]}). Precision is defined.")
                
            return res, total_pos_preds, precision_undefined

    gen_metrics, gen_pos_preds, gen_prec_undefined = get_metrics_and_check_warning(gen_probe, X_gen_test_scaled, y_gen_test, "Linear Generalization Probe")
    
    logger.info("=== Held-Out Generalization Evaluation (Linear, Scaled) ===")
    logger.info(f"Generalization Accuracy : {gen_metrics['accuracy']:.4f}")
    if gen_prec_undefined:
        logger.info("Generalization Precision: UNDEFINED (Zero positive predictions made)")
    else:
        logger.info(f"Generalization Precision: {gen_metrics['precision']:.4f}")
    logger.info(f"Generalization Recall   : {gen_metrics['recall']:.4f}")
    logger.info(f"Generalization F1 Score : {gen_metrics['f1']:.4f}")
    logger.info("\nGeneralization Confusion Matrix:\n" + str(gen_metrics['confusion_matrix']))
    
    # Train and evaluate MLP Probe
    logger.info("Training MLP Probe on Generalization split...")
    gen_mlp_probe = train_probe(X_gen_train_scaled, y_gen_train, use_mlp=True)
    gen_mlp_metrics, gen_mlp_pos_preds, gen_mlp_prec_undefined = get_metrics_and_check_warning(gen_mlp_probe, X_gen_test_scaled, y_gen_test, "MLP Generalization Probe")
    
    logger.info("=== Held-Out Generalization Evaluation (MLP, Scaled) ===")
    logger.info(f"Generalization MLP Accuracy : {gen_mlp_metrics['accuracy']:.4f}")
    if gen_mlp_prec_undefined:
        logger.info("Generalization MLP Precision: UNDEFINED (Zero positive predictions made)")
    else:
        logger.info(f"Generalization MLP Precision: {gen_mlp_metrics['precision']:.4f}")
    logger.info(f"Generalization MLP Recall   : {gen_mlp_metrics['recall']:.4f}")
    logger.info(f"Generalization MLP F1 Score : {gen_mlp_metrics['f1']:.4f}")
    logger.info("\nGeneralization MLP Confusion Matrix:\n" + str(gen_mlp_metrics['confusion_matrix']))
    
    # Summary block
    print("\n" + "="*50)
    print(" PIPELINE PROCESS COMPLETE - SUMMARY (SCALED)")
    print("="*50)
    print(f"Best Representation: {best_rep}")
    print(f"Best Layers (Ranked): {[item[0] for item in best_rankings[:5]]}")
    print(f"Selected Probe Layers: {selected_layers}")
    print(f"Validation F1 (Linear): {metrics['f1']:.4f}")
    print(f"Validation F1 (MLP)   : {mlp_metrics['f1']:.4f}")
    print(f"Validation Confusion Matrix (Linear):\n{metrics['confusion_matrix']}")
    print("-"*50)
    
    # Generalization output details
    prec_str_lin = "UNDEFINED" if gen_prec_undefined else f"{gen_metrics['precision']:.4f}"
    prec_str_mlp = "UNDEFINED" if gen_mlp_prec_undefined else f"{gen_mlp_metrics['precision']:.4f}"
    
    print(f"Held-Out Generalization F1 (Linear): {gen_metrics['f1']:.4f}")
    print(f"Generalization Precision (Linear)  : {prec_str_lin} (Positive predictions: {gen_pos_preds})")
    print(f"Generalization Recall (Linear)     : {gen_metrics['recall']:.4f}")
    print(f"Held-Out Confusion Matrix (Linear):\n{gen_metrics['confusion_matrix']}")
    print("-"*50)
    print(f"Held-Out Generalization F1 (MLP)   : {gen_mlp_metrics['f1']:.4f}")
    print(f"Generalization Precision (MLP)     : {prec_str_mlp} (Positive predictions: {gen_mlp_pos_preds})")
    print(f"Generalization Recall (MLP)        : {gen_mlp_metrics['recall']:.4f}")
    print(f"Held-Out Confusion Matrix (MLP):\n{gen_mlp_metrics['confusion_matrix']}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
