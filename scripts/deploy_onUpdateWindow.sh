gcloud functions deploy onUpdateWindow \
  --entry-point onUpdateWindow \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/windows/{window}" \
  --memory=512MB
