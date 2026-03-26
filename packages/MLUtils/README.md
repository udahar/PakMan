# ML Utilities Module

Train/val/test splitting, model serialization, and evaluation metrics.

## Quick Start

```python
from modules.ml_utilities import train_validate_test_split, EvaluationMetrics, ModelPickler

# Split data
X_train, X_val, X_test, y_train, y_val, y_test = train_validate_test_split(X, y)

# Evaluate
metrics = EvaluationMetrics()
print(metrics.accuracy(y_true, y_pred))
print(metrics.f1(y_true, y_pred))

# Save/load model
ModelPickler.save(model, "model.pkl")
model = ModelPickler.load("model.pkl")
```

## Components

- **TrainValidateTestSplitter** - Data splitting
- **CrossValidator** - K-fold cross-validation
- **EvaluationMetrics** - Classification/regression metrics
- **ModelPickler** - Model serialization (pickle/joblib)
