gcloud functions deploy onNewFrame \
  --entry-point onNewFrame \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/frames/{f}" \
  --memory=512MB