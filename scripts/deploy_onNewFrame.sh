gcloud functions deploy onNewFrame \
  --entry-point onNewFrame \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/frames/{sample}" \
  --memory=512MB