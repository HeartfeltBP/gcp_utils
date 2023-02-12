gcloud functions deploy onNewSample \
  --entry-point onValidSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/processed_samples/{sample}"