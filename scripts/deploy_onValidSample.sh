gcloud functions deploy onValidSample \
  --entry-point onValidSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/processed_samples/{sample}" \
  --memory=512MB