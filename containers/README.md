# Containerized ML Pipeline

The containerized ML pipeline is build from 5 components:

1. **Flow Generator** using Locust.

2. **Preprocessing** stage rescaling the features of a flow.

3. **Anomaly Detector** differentiating `Benign` flows from `Attacks`.

4. **Multi-Class Classifier** classifies previously detected attacks to one of the known attacks.

5. **Zero-day Detector** correcting previously detected flows with a low confidence belonging to any of the known attacks either as `Benign` or true `Unknown`.

For more details regarding any of the components, look in the corresponding subdirectory.

## Test ML Pipeline Locally

The ML pipeline can easily be deployed on a single machine using `docker compose build` followed by `docker compose up`.
