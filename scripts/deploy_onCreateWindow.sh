gcloud functions deploy onCreateWindow \
  --entry-point onCreateWindow \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/windows/{window}" \
  --memory=512MB
