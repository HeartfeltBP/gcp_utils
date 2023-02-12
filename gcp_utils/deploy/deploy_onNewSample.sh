gcloud functions deploy onNewSample2 \
  --entry-point onNewSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/new_samples/{sample}"