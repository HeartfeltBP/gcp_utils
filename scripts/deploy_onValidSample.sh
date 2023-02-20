gcloud functions deploy onValidSample \
  --entry-point onValidSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/samples/{s}" \
  --memory=512MB