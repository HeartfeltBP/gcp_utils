gcloud functions deploy onNewSample \
  --entry-point onNewSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/data/{sample}" \
  --memory=512MB