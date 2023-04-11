gcloud functions deploy onUpdateFrame \
  --entry-point onUpdateFrame \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/frames/{frame}" \
  --memory=512MB
