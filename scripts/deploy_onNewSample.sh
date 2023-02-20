gcloud functions deploy onNewSample \
  --entry-point onNewSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/samples/{s}" \
  --memory=512MB